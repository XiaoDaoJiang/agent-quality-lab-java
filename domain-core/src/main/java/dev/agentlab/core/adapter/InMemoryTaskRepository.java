package dev.agentlab.core.adapter;

import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.function.UnaryOperator;

import dev.agentlab.core.domain.Task;
import dev.agentlab.core.domain.TaskNotFoundException;
import dev.agentlab.core.ports.TaskRepository;

/** Test-lab storage only: data is volatile and capacity is not bounded. */
public final class InMemoryTaskRepository implements TaskRepository {
    private final ConcurrentMap<UUID, Task> tasks = new ConcurrentHashMap<>();

    @Override
    public void insert(Task task) {
        Objects.requireNonNull(task, "task");
        if (tasks.putIfAbsent(task.getId(), task) != null) {
            throw new IllegalStateException("Duplicate task id");
        }
    }

    @Override
    public Optional<Task> find(UUID id) {
        return Optional.ofNullable(tasks.get(Objects.requireNonNull(id, "id")));
    }

    @Override
    public Task update(UUID id, UnaryOperator<Task> transition) {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(transition, "transition");
        return tasks.compute(id, (key, current) -> {
            if (current == null) {
                throw new TaskNotFoundException(key);
            }
            Task next = Objects.requireNonNull(transition.apply(current), "transition result");
            if (!key.equals(next.getId())) {
                throw new IllegalArgumentException("A transition cannot change the task id");
            }
            return next;
        });
    }
}
