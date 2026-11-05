package dev.agentlab.core.ports;

import java.util.Optional;
import java.util.UUID;
import java.util.function.UnaryOperator;

import dev.agentlab.core.domain.Task;

public interface TaskRepository {
    void insert(Task task);

    Optional<Task> find(UUID id);

    /** Apply a transition atomically for one id; throw if the task does not exist. */
    Task update(UUID id, UnaryOperator<Task> transition);
}
