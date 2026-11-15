package com.traffic.supervision.controller;

import com.traffic.supervision.dto.SimulationStatusDTO;
import com.traffic.supervision.dto.StartSimulationRequest;
import com.traffic.supervision.entity.SimulationRun;
import com.traffic.supervision.service.SimulationRunService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/simulation")
public class SimulationController {

    private final SimulationRunService simulationRunService;

    public SimulationController(SimulationRunService simulationRunService) {
        this.simulationRunService = simulationRunService;
    }

    @PostMapping("/start")
    public ResponseEntity<SimulationRun> start(@RequestBody(required = false) StartSimulationRequest request) {
        if (request == null) {
            request = new StartSimulationRequest();
        }
        SimulationRun run = simulationRunService.start(request);
        return ResponseEntity.ok(run);
    }

    @PostMapping("/stop")
    public ResponseEntity<Map<String, Object>> stop() {
        Map<String, Object> res = simulationRunService.stop();
        return ResponseEntity.ok(res);
    }

    @GetMapping("/status")
    public ResponseEntity<SimulationStatusDTO> getStatus() {
        return ResponseEntity.ok(simulationRunService.getStatus());
    }
}
