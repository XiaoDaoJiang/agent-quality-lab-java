package dev.agentlab.core.domain;

import java.util.Objects;
import java.util.UUID;

/** An immutable task. Terminal transitions cannot be bypassed through setters. */
public final class Task {
    private static final int MAX_TITLE_LENGTH = 120;
    private final UUID id;
    private final String title;
    private final TaskStatus status;

    private Task(UUID id, String title, TaskStatus status) {
        this.id = Objects.requireNonNull(id, "id");
        this.title = title;
        this.status = Objects.requireNonNull(status, "status");
    }

    public static Task create(UUID id, String title) {
        if (title == null || title.trim().isEmpty()) {
            throw new IllegalArgumentException("title must not be blank");
        }
        String normalized = title.trim();
        if (normalized.length() > MAX_TITLE_LENGTH) {
            throw new IllegalArgumentException("title must be at most 120 UTF-16 code units");
        }
        return new Task(id, normalized, TaskStatus.TODO);
    }

    public Task complete() {
        if (status == TaskStatus.CANCELLED) {
            throw new IllegalStateException("A cancelled task cannot be completed");
        }
        return status == TaskStatus.DONE ? this : new Task(id, title, TaskStatus.DONE);
    }

    public Task cancel() {
        if (status == TaskStatus.DONE) {
            throw new IllegalStateException("A completed task cannot be cancelled");
        }
        return status == TaskStatus.CANCELLED ? this : new Task(id, title, TaskStatus.CANCELLED);
    }

    public UUID getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public TaskStatus getStatus() {
        return status;
    }
}
