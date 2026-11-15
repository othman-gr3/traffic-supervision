package com.traffic.supervision.dto;

public class StartSimulationRequest {
    private String controller = "smart"; // "fixed" or "smart"
    private Integer seed = 1;
    private Integer duration = 1800; // default 30 min (1800s)
    private String net;
    private String routes;
    private String tls;
    private Integer greenA = 35;
    private Integer greenB = 35;
    private Double stepDelay = 0.2; // default 0.2s for testing / streaming (set 1.0 for real-time)

    public StartSimulationRequest() {
    }

    public Double getStepDelay() {
        return stepDelay;
    }

    public void setStepDelay(Double stepDelay) {
        this.stepDelay = stepDelay;
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

    public String getNet() {
        return net;
    }

    public void setNet(String net) {
        this.net = net;
    }

    public String getRoutes() {
        return routes;
    }

    public void setRoutes(String routes) {
        this.routes = routes;
    }

    public String getTls() {
        return tls;
    }

    public void setTls(String tls) {
        this.tls = tls;
    }

    public Integer getGreenA() {
        return greenA;
    }

    public void setGreenA(Integer greenA) {
        this.greenA = greenA;
    }

    public Integer getGreenB() {
        return greenB;
    }

    public void setGreenB(Integer greenB) {
        this.greenB = greenB;
    }
}
