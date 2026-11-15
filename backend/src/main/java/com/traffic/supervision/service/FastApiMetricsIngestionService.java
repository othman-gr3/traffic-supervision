package com.traffic.supervision.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.traffic.supervision.config.WebSocketConfig;
import com.traffic.supervision.entity.RoadMetricSnapshot;
import com.traffic.supervision.entity.SimulationRun;
import com.traffic.supervision.repository.RoadMetricSnapshotRepository;
import com.traffic.supervision.repository.SimulationRunRepository;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.*;
import org.springframework.web.socket.client.standard.StandardWebSocketClient;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.net.URI;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
public class FastApiMetricsIngestionService {

    private static final Logger log = LoggerFactory.getLogger(FastApiMetricsIngestionService.class);

    @Value("${fastapi.ws-url}")
    private String fastApiWsUrl;

    private final SimulationRunRepository runRepository;
    private final RoadMetricSnapshotRepository snapshotRepository;
    private final WebSocketConfig webSocketConfig;
    private final ObjectMapper objectMapper;

    private WebSocketSession clientSession;
    private Long activeRunId = null;
    private int frameCountForCurrentRun = 0;
    private final AtomicBoolean isConnecting = new AtomicBoolean(false);

    public FastApiMetricsIngestionService(SimulationRunRepository runRepository,
                                         RoadMetricSnapshotRepository snapshotRepository,
                                         WebSocketConfig webSocketConfig) {
        this.runRepository = runRepository;
        this.snapshotRepository = snapshotRepository;
        this.webSocketConfig = webSocketConfig;
        this.objectMapper = new ObjectMapper();
    }

    @PostConstruct
    public void init() {
        ensureConnected();
    }

    public synchronized void setActiveRunId(Long runId) {
        this.activeRunId = runId;
        this.frameCountForCurrentRun = 0;
        ensureConnected();
    }

    public synchronized Long getActiveRunId() {
        return activeRunId;
    }

    public void ensureConnected() {
        if (clientSession != null && clientSession.isOpen()) {
            return;
        }
        if (isConnecting.get()) {
            return;
        }

        isConnecting.set(true);
        StandardWebSocketClient client = new StandardWebSocketClient();
        try {
            client.execute(new TextWebSocketHandler() {
                @Override
                public void afterConnectionEstablished(WebSocketSession session) {
                    clientSession = session;
                    isConnecting.set(false);
                    log.info("Connected to FastAPI WebSocket at {}", fastApiWsUrl);
                }

                @Override
                protected void handleTextMessage(WebSocketSession session, TextMessage message) {
                    handleIncomingFrame(message.getPayload());
                }

                @Override
                public void handleTransportError(WebSocketSession session, Throwable exception) {
                    log.warn("FastAPI WebSocket transport error: {}", exception.getMessage());
                    isConnecting.set(false);
                }

                @Override
                public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
                    log.info("FastAPI WebSocket disconnected: {}", status);
                    clientSession = null;
                    isConnecting.set(false);
                }
            }, null, URI.create(fastApiWsUrl));
        } catch (Exception e) {
            log.error("Could not connect to FastAPI WebSocket: {}", e.getMessage());
            isConnecting.set(false);
        }
    }

    private void handleIncomingFrame(String payload) {
        log.info("Incoming WebSocket frame: {}", payload.substring(0, Math.min(80, payload.length())));
        // Broadcast raw message to frontend subscribers on ws://localhost:8080/ws/live
        webSocketConfig.getLiveMetricsHandler().broadcast(payload);

        try {
            JsonNode root = objectMapper.readTree(payload);

            // Ignore heartbeat
            if (root.has("heartbeat")) {
                String status = root.path("status").asText();
                if ("finished".equalsIgnoreCase(status) && activeRunId != null && frameCountForCurrentRun > 0) {
                    finalizeActiveRun("COMPLETED");
                }
                return;
            }

            if (!root.has("time") || activeRunId == null) {
                return;
            }

            frameCountForCurrentRun++;

            int timeStep = root.path("time").asInt();
            JsonNode roadsNode = root.path("roads");
            JsonNode lightNode = root.path("light");

            String lightAxis = lightNode.path("axis").asText(null);
            String lightStage = lightNode.path("stage").asText(null);

            SimulationRun run = runRepository.findById(activeRunId).orElse(null);
            if (run == null) {
                return;
            }

            List<RoadMetricSnapshot> snapshots = new ArrayList<>();
            double totalSpeedSum = 0;
            int speedCount = 0;
            double maxWaitRecorded = 0;
            double avgWaitSum = 0;
            int waitCount = 0;
            int totalCrossed = 0;

            if (roadsNode.isArray()) {
                for (JsonNode road : roadsNode) {
                    RoadMetricSnapshot s = new RoadMetricSnapshot();
                    s.setRun(run);
                    s.setTimeStep(timeStep);
                    s.setRoadName(road.path("road").asText());
                    s.setEdgeId(road.path("edge").asText());
                    s.setVehiclesCount(road.path("vehicles").asInt(0));
                    s.setQueueLength(road.path("queue").asInt(0));
                    s.setAvgSpeed(road.path("avg_speed").asDouble(0.0));
                    s.setCurrentMaxWait(road.path("current_max_wait").asDouble(0.0));
                    s.setAvgWait(road.path("avg_wait").asDouble(0.0));
                    s.setMaxWait(road.path("max_wait").asDouble(0.0));
                    int crossed = road.path("crossed").asInt(0);
                    s.setCrossedCount(crossed);
                    s.setLightAxis(lightAxis);
                    s.setLightStage(lightStage);

                    snapshots.add(s);

                    if (s.getAvgSpeed() > 0) {
                        totalSpeedSum += s.getAvgSpeed();
                        speedCount++;
                    }
                    if (s.getMaxWait() > maxWaitRecorded) {
                        maxWaitRecorded = s.getMaxWait();
                    }
                    if (s.getAvgWait() > 0) {
                        avgWaitSum += s.getAvgWait();
                        waitCount++;
                    }
                    totalCrossed += crossed;
                }
            }

            snapshotRepository.saveAll(snapshots);

            // Update run running stats
            run.setTotalCrossed(totalCrossed);
            if (maxWaitRecorded > 0) {
                run.setOverallMaxWait(maxWaitRecorded);
            }
            if (waitCount > 0) {
                run.setOverallAvgWait(Math.round((avgWaitSum / waitCount) * 100.0) / 100.0);
            }
            if (speedCount > 0) {
                run.setOverallAvgSpeed(Math.round((totalSpeedSum / speedCount) * 100.0) / 100.0);
            }
            runRepository.save(run);

            // If time reaches duration, finalize
            if (run.getDuration() != null && timeStep >= run.getDuration()) {
                finalizeActiveRun("COMPLETED");
            }

        } catch (Exception e) {
            log.warn("Error processing metrics frame: {}", e.getMessage());
        }
    }

    public synchronized void finalizeActiveRun(String status) {
        if (activeRunId == null) {
            return;
        }
        runRepository.findById(activeRunId).ifPresent(run -> {
            run.setStatus(status);
            run.setEndTime(LocalDateTime.now());
            runRepository.save(run);
            log.info("Simulation run #{} marked as {}", run.getId(), status);
        });
        activeRunId = null;
    }

    @PreDestroy
    public void cleanup() {
        if (clientSession != null && clientSession.isOpen()) {
            try {
                clientSession.close();
            } catch (IOException ignored) {
            }
        }
    }
}
