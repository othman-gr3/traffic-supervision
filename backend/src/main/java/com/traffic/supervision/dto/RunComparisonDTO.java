package com.traffic.supervision.dto;

import com.traffic.supervision.entity.SimulationRun;

public class RunComparisonDTO {
    private SimulationRun run1;
    private SimulationRun run2;
    private Double avgWaitDiffPercent;
    private Double maxWaitDiffPercent;
    private Double avgSpeedDiffPercent;
    private Integer throughputDiff;

    public RunComparisonDTO() {
    }

    public RunComparisonDTO(SimulationRun run1, SimulationRun run2) {
        this.run1 = run1;
        this.run2 = run2;
        calculateDiffs();
    }

    private void calculateDiffs() {
        if (run1 != null && run2 != null) {
            if (run1.getOverallAvgWait() != null && run2.getOverallAvgWait() != null && run1.getOverallAvgWait() > 0) {
                this.avgWaitDiffPercent = ((run2.getOverallAvgWait() - run1.getOverallAvgWait()) / run1.getOverallAvgWait()) * 100.0;
            }
            if (run1.getOverallMaxWait() != null && run2.getOverallMaxWait() != null && run1.getOverallMaxWait() > 0) {
                this.maxWaitDiffPercent = ((run2.getOverallMaxWait() - run1.getOverallMaxWait()) / run1.getOverallMaxWait()) * 100.0;
            }
            if (run1.getOverallAvgSpeed() != null && run2.getOverallAvgSpeed() != null && run1.getOverallAvgSpeed() > 0) {
                this.avgSpeedDiffPercent = ((run2.getOverallAvgSpeed() - run1.getOverallAvgSpeed()) / run1.getOverallAvgSpeed()) * 100.0;
            }
            if (run1.getTotalCrossed() != null && run2.getTotalCrossed() != null) {
                this.throughputDiff = run2.getTotalCrossed() - run1.getTotalCrossed();
            }
        }
    }

    public SimulationRun getRun1() {
        return run1;
    }

    public void setRun1(SimulationRun run1) {
        this.run1 = run1;
    }

    public SimulationRun getRun2() {
        return run2;
    }

    public void setRun2(SimulationRun run2) {
        this.run2 = run2;
    }

    public Double getAvgWaitDiffPercent() {
        return avgWaitDiffPercent;
    }

    public void setAvgWaitDiffPercent(Double avgWaitDiffPercent) {
        this.avgWaitDiffPercent = avgWaitDiffPercent;
    }

    public Double getMaxWaitDiffPercent() {
        return maxWaitDiffPercent;
    }

    public void setMaxWaitDiffPercent(Double maxWaitDiffPercent) {
        this.maxWaitDiffPercent = maxWaitDiffPercent;
    }

    public Double getAvgSpeedDiffPercent() {
        return avgSpeedDiffPercent;
    }

    public void setAvgSpeedDiffPercent(Double avgSpeedDiffPercent) {
        this.avgSpeedDiffPercent = avgSpeedDiffPercent;
    }

    public Integer getThroughputDiff() {
        return throughputDiff;
    }

    public void setThroughputDiff(Integer throughputDiff) {
        this.throughputDiff = throughputDiff;
    }
}
