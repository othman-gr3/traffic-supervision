package com.traffic.supervision.repository;

import com.traffic.supervision.entity.SimulationRun;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SimulationRunRepository extends JpaRepository<SimulationRun, Long> {

    List<SimulationRun> findAllByOrderByStartTimeDesc();

    Optional<SimulationRun> findFirstByStatusOrderByStartTimeDesc(String status);
}
