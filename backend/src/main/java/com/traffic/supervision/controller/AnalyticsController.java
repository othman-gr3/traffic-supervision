package com.traffic.supervision.controller;

import com.traffic.supervision.dto.RunComparisonDTO;
import com.traffic.supervision.entity.RoadMetricSnapshot;
import com.traffic.supervision.entity.SimulationRun;
import com.traffic.supervision.service.SimulationRunService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/runs")
public class AnalyticsController {

    private final SimulationRunService simulationRunService;

    public AnalyticsController(SimulationRunService simulationRunService) {
        this.simulationRunService = simulationRunService;
    }

    @GetMapping
    public ResponseEntity<List<SimulationRun>> getAllRuns() {
        return ResponseEntity.ok(simulationRunService.getAllRuns());
    }

    @GetMapping("/{id}")
    public ResponseEntity<SimulationRun> getRunById(@PathVariable Long id) {
        return simulationRunService.getRunById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/metrics")
    public ResponseEntity<List<RoadMetricSnapshot>> getRunMetrics(
            @PathVariable Long id,
            @RequestParam(defaultValue = "1") int sampleRate) {
        return ResponseEntity.ok(simulationRunService.getRunMetrics(id, sampleRate));
    }

    @GetMapping("/compare")
    public ResponseEntity<RunComparisonDTO> compareRuns(
            @RequestParam Long run1,
            @RequestParam Long run2) {
        return ResponseEntity.ok(simulationRunService.compareRuns(run1, run2));
    }
}
