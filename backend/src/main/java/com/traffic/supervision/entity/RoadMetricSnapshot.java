package com.traffic.supervision.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "road_metric_snapshots", indexes = {
    @Index(name = "idx_run_time", columnList = "run_id, time_step")
})
public class RoadMetricSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "run_id", nullable = false)
    private SimulationRun run;

    @Column(name = "time_step", nullable = false)
    private Integer timeStep;

    @Column(name = "road_name", nullable = false)
    private String roadName;

    @Column(name = "edge_id", nullable = false)
    private String edgeId;

    @Column(name = "vehicles_count")
    private Integer vehiclesCount;

    @Column(name = "queue_length")
    private Integer queueLength;

    @Column(name = "avg_speed")
    private Double avgSpeed;

    @Column(name = "current_max_wait")
    private Double currentMaxWait;

    @Column(name = "avg_wait")
    private Double avgWait;

    @Column(name = "max_wait")
    private Double maxWait;

    @Column(name = "crossed_count")
    private Integer crossedCount;

    @Column(name = "light_axis")
    private String lightAxis;

    @Column(name = "light_stage")
    private String lightStage;

    public RoadMetricSnapshot() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    @com.fasterxml.jackson.annotation.JsonIgnore
    public SimulationRun getRun() {
        return run;
    }

    @com.fasterxml.jackson.annotation.JsonProperty("runId")
    public Long getRunId() {
        return run != null ? run.getId() : null;
    }

    public void setRun(SimulationRun run) {
        this.run = run;
    }

    public Integer getTimeStep() {
        return timeStep;
    }

    public void setTimeStep(Integer timeStep) {
        this.timeStep = timeStep;
    }

    public String getRoadName() {
        return roadName;
    }

    public void setRoadName(String roadName) {
        this.roadName = roadName;
    }

    public String getEdgeId() {
        return edgeId;
    }

    public void setEdgeId(String edgeId) {
        this.edgeId = edgeId;
    }

    public Integer getVehiclesCount() {
        return vehiclesCount;
    }

    public void setVehiclesCount(Integer vehiclesCount) {
        this.vehiclesCount = vehiclesCount;
    }

    public Integer getQueueLength() {
        return queueLength;
    }

    public void setQueueLength(Integer queueLength) {
        this.queueLength = queueLength;
    }

    public Double getAvgSpeed() {
        return avgSpeed;
    }

    public void setAvgSpeed(Double avgSpeed) {
        this.avgSpeed = avgSpeed;
    }

    public Double getCurrentMaxWait() {
        return currentMaxWait;
    }

    public void setCurrentMaxWait(Double currentMaxWait) {
        this.currentMaxWait = currentMaxWait;
    }

    public Double getAvgWait() {
        return avgWait;
    }

    public void setAvgWait(Double avgWait) {
        this.avgWait = avgWait;
    }

    public Double getMaxWait() {
        return maxWait;
    }

    public void setMaxWait(Double maxWait) {
        this.maxWait = maxWait;
    }

    public Integer getCrossedCount() {
        return crossedCount;
    }

    public void setCrossedCount(Integer crossedCount) {
        this.crossedCount = crossedCount;
    }

    public String getLightAxis() {
        return lightAxis;
    }

    public void setLightAxis(String lightAxis) {
        this.lightAxis = lightAxis;
    }

    public String getLightStage() {
        return lightStage;
    }

    public void setLightStage(String lightStage) {
        this.lightStage = lightStage;
    }
}
