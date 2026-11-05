package dev.agentlab.core.domain;

import java.util.UUID;

public final class TaskNotFoundException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public TaskNotFoundException(UUID id) {
        super("Task not found: " + id);
    }
}
