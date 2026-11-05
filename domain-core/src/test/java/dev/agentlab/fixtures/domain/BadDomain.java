package dev.agentlab.fixtures.domain;

import dev.agentlab.core.adapter.InMemoryTaskRepository;

/** Deliberate architecture violation, isolated to test sources. */
public final class BadDomain {
    public InMemoryTaskRepository repository() {
        return new InMemoryTaskRepository();
    }
}
