package dev.agentlab.app.fixtures.web;

import dev.agentlab.core.adapter.InMemoryTaskRepository;

/** Deliberate architecture violation, not a Spring bean or production source. */
public final class BadController {
    public InMemoryTaskRepository repository() {
        return new InMemoryTaskRepository();
    }
}
