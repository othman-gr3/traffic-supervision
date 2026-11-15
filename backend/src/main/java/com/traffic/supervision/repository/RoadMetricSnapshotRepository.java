package com.traffic.supervision.repository;

import com.traffic.supervision.entity.RoadMetricSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RoadMetricSnapshotRepository extends JpaRepository<RoadMetricSnapshot, Long> {

    List<RoadMetricSnapshot> findByRun_IdOrderByTimeStepAsc(Long runId);

    @Query("SELECT r FROM RoadMetricSnapshot r WHERE r.run.id = :runId AND (MOD(r.timeStep, :sampleRate) = 0 OR r.timeStep = 1) ORDER BY r.timeStep ASC")
    List<RoadMetricSnapshot> findSampledByRunId(@Param("runId") Long runId, @Param("sampleRate") int sampleRate);
}
