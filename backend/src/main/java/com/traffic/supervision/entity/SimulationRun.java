package com.traffic.supervision.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "simulation_runs")
public class SimulationRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String controller; // "fixed" or "smart"

    @Column(nullable = false)
    private Integer seed;

    @Column(nullable = false)
    private Integer duration;

    @Column(nullable = false)
    private String status; // "RUNNING", "COMPLETED", "STOPPED", "FAILED"

    @Column(name = "start_time")
    private LocalDateTime startTime;

    @Column(name = "end_time")
    private LocalDateTime endTime;

    @Column(name = "total_crossed")
    private Integer totalCrossed = 0;

    @Column(name = "overall_avg_wait")
    private Double overallAvgWait = 0.0;

    @Column(name = "overall_max_wait")
    private Double overallMaxWait = 0.0;

    @Column(name = "overall_avg_speed")
    private Double overallAvgSpeed = 0.0;

    @Column(name = "tls_id")
    private String tlsId;

    public SimulationRun() {
    }

    public SimulationRun(String controller, Integer seed, Integer duration, String tlsId) {
        this.controller = controller;
        this.seed = seed;
        this.duration = duration;
        this.tlsId = tlsId;
        this.status = "RUNNING";
        this.startTime = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getController() {
        return controller;
    }

    public void setController(String controller) {
        this.controller = controller;
    }

    public Integer getSeed() {
        return seed;
    }

    public void setSeed(Integer seed) {
        this.seed = seed;
    }

    public Integer getDuration() {
        return duration;
    }

    public void setDuration(Integer duration) {
        this.duration = duration;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public LocalDateTime getStartTime() {
        return startTime;
    }

    public void setStartTime(LocalDateTime startTime) {
        this.startTime = startTime;
    }

    public LocalDateTime getEndTime() {
        return endTime;
    }

    public void setEndTime(LocalDateTime endTime) {
        this.endTime = endTime;
    }

    public Integer getTotalCrossed() {
        return totalCrossed;
    }

    public void setTotalCrossed(Integer totalCrossed) {
        this.totalCrossed = totalCrossed;
    }

    public Double getOverallAvgWait() {
        return overallAvgWait;
    }

    public void setOverallAvgWait(Double overallAvgWait) {
        this.overallAvgWait = overallAvgWait;
    }

    public Double getOverallMaxWait() {
        return overallMaxWait;
    }

    public void setOverallMaxWait(Double overallMaxWait) {
        this.overallMaxWait = overallMaxWait;
    }

    public Double getOverallAvgSpeed() {
        return overallAvgSpeed;
    }

    public void setOverallAvgSpeed(Double overallAvgSpeed) {
        this.overallAvgSpeed = overallAvgSpeed;
    }

    public String getTlsId() {
        return tlsId;
    }

    public void setTlsId(String tlsId) {
        this.tlsId = tlsId;
    }
}
