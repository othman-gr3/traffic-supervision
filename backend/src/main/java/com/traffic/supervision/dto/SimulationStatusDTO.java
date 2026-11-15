package com.traffic.supervision.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class SimulationStatusDTO {
    private String status;
    private String controller;
    private Integer seed;
    private Integer duration;

    @JsonProperty("current_time")
    private Integer currentTime;

    private String error;
    private Long activeRunId;

    public SimulationStatusDTO() {
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
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

    public Integer getCurrentTime() {
        return currentTime;
    }

    public void setCurrentTime(Integer currentTime) {
        this.currentTime = currentTime;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public Long getActiveRunId() {
        return activeRunId;
    }

    public void setActiveRunId(Long activeRunId) {
        this.activeRunId = activeRunId;
    }
}
