package dev.agentlab.core.application;

import java.util.Objects;
import java.util.UUID;

import dev.agentlab.core.domain.Task;
import dev.agentlab.core.domain.TaskNotFoundException;
import dev.agentlab.core.ports.TaskRepository;

public final class TaskService {
    private final TaskRepository repository;

    public TaskService(TaskRepository repository) {
        this.repository = Objects.requireNonNull(repository, "repository");
    }

    public Task create(String title) {
        Task task = Task.create(UUID.randomUUID(), title);
        repository.insert(task);
        return task;
    }

    public Task get(UUID id) {
        Objects.requireNonNull(id, "id");
        return repository.find(id).orElseThrow(() -> new TaskNotFoundException(id));
    }

    public Task complete(UUID id) {
        return repository.update(Objects.requireNonNull(id, "id"), Task::complete);
    }

    public Task cancel(UUID id) {
        return repository.update(Objects.requireNonNull(id, "id"), Task::cancel);
    }
}
