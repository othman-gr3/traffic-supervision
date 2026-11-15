package com.traffic.supervision.service;

import com.traffic.supervision.dto.RunComparisonDTO;
import com.traffic.supervision.dto.SimulationStatusDTO;
import com.traffic.supervision.dto.StartSimulationRequest;
import com.traffic.supervision.entity.RoadMetricSnapshot;
import com.traffic.supervision.entity.SimulationRun;
import com.traffic.supervision.repository.RoadMetricSnapshotRepository;
import com.traffic.supervision.repository.SimulationRunRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class SimulationRunService {

    private final SimulationRunRepository runRepository;
    private final RoadMetricSnapshotRepository snapshotRepository;
    private final FastApiClientService fastApiClientService;
    private final FastApiMetricsIngestionService ingestionService;

    @Value("${simulation.default.tls}")
    private String defaultTls;

    public SimulationRunService(SimulationRunRepository runRepository,
                                  RoadMetricSnapshotRepository snapshotRepository,
                                  FastApiClientService fastApiClientService,
                                  FastApiMetricsIngestionService ingestionService) {
        this.runRepository = runRepository;
        this.snapshotRepository = snapshotRepository;
        this.fastApiClientService = fastApiClientService;
        this.ingestionService = ingestionService;
    }

    public SimulationRun start(StartSimulationRequest request) {
        // 1. Create a new simulation run in DB
        String tlsId = request.getTls() != null && !request.getTls().isBlank() ? request.getTls() : defaultTls;
        SimulationRun run = new SimulationRun(
                request.getController(),
                request.getSeed(),
                request.getDuration(),
                tlsId
        );
        run = runRepository.save(run);

        // 2. Set active run for ingestion
        ingestionService.setActiveRunId(run.getId());

        // 3. Trigger FastAPI /start
        try {
            fastApiClientService.startSimulation(request);
        } catch (Exception e) {
            run.setStatus("FAILED");
            runRepository.save(run);
            ingestionService.setActiveRunId(null);
            throw new RuntimeException("Failed to start simulation in FastAPI: " + e.getMessage(), e);
        }

        return run;
    }

    public Map<String, Object> stop() {
        Map<String, Object> result = fastApiClientService.stopSimulation();
        ingestionService.finalizeActiveRun("STOPPED");
        return result;
    }

    public SimulationStatusDTO getStatus() {
        SimulationStatusDTO status = fastApiClientService.getStatus();
        status.setActiveRunId(ingestionService.getActiveRunId());
        return status;
    }

    public List<SimulationRun> getAllRuns() {
        return runRepository.findAllByOrderByStartTimeDesc();
    }

    public Optional<SimulationRun> getRunById(Long id) {
        return runRepository.findById(id);
    }

    public List<RoadMetricSnapshot> getRunMetrics(Long id, int sampleRate) {
        if (sampleRate <= 1) {
            return snapshotRepository.findByRun_IdOrderByTimeStepAsc(id);
        }
        return snapshotRepository.findSampledByRunId(id, sampleRate);
    }

    public RunComparisonDTO compareRuns(Long id1, Long id2) {
        SimulationRun run1 = runRepository.findById(id1)
                .orElseThrow(() -> new IllegalArgumentException("Run not found: " + id1));
        SimulationRun run2 = runRepository.findById(id2)
                .orElseThrow(() -> new IllegalArgumentException("Run not found: " + id2));
        return new RunComparisonDTO(run1, run2);
    }
}
