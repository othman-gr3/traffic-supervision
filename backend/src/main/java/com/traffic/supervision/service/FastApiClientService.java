package com.traffic.supervision.service;

import com.traffic.supervision.dto.SimulationStatusDTO;
import com.traffic.supervision.dto.StartSimulationRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class FastApiClientService {

    private final RestTemplate restTemplate;

    @Value("${fastapi.base-url}")
    private String fastApiBaseUrl;

    @Value("${simulation.default.net}")
    private String defaultNet;

    @Value("${simulation.default.routes}")
    private String defaultRoutes;

    @Value("${simulation.default.tls}")
    private String defaultTls;

    public FastApiClientService() {
        this.restTemplate = new RestTemplate();
    }

    public Map<String, Object> startSimulation(StartSimulationRequest request) {
        String url = fastApiBaseUrl + "/start";

        Map<String, Object> body = new HashMap<>();
        body.put("controller", request.getController());
        body.put("seed", request.getSeed());
        body.put("duration", request.getDuration());
        body.put("net", request.getNet() != null && !request.getNet().isBlank() ? request.getNet() : defaultNet);
        body.put("routes", request.getRoutes() != null && !request.getRoutes().isBlank() ? request.getRoutes() : defaultRoutes);
        body.put("tls", request.getTls() != null && !request.getTls().isBlank() ? request.getTls() : defaultTls);
        body.put("green_a", request.getGreenA() != null ? request.getGreenA() : 35);
        body.put("green_b", request.getGreenB() != null ? request.getGreenB() : 35);
        body.put("step_delay", request.getStepDelay() != null ? request.getStepDelay() : 0.2);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
        return response.getBody();
    }

    public Map<String, Object> stopSimulation() {
        String url = fastApiBaseUrl + "/stop";
        ResponseEntity<Map> response = restTemplate.postForEntity(url, null, Map.class);
        return response.getBody();
    }

    public SimulationStatusDTO getStatus() {
        String url = fastApiBaseUrl + "/status";
        return restTemplate.getForObject(url, SimulationStatusDTO.class);
    }
}
