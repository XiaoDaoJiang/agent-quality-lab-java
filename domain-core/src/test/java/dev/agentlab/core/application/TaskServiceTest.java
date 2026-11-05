package dev.agentlab.core.application;

import java.util.UUID;

import org.junit.jupiter.api.Test;

import dev.agentlab.core.adapter.InMemoryTaskRepository;
import dev.agentlab.core.compat.LegacyCustomerRow;
import dev.agentlab.core.domain.Task;
import dev.agentlab.core.domain.TaskNotFoundException;
import dev.agentlab.core.domain.TaskStatus;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class TaskServiceTest {
    private final TaskService service = new TaskService(new InMemoryTaskRepository());

    @Test
    void createsReadsAndCompletes() {
        Task created = service.create("Ship regression test");
        assertEquals(created.getId(), service.get(created.getId()).getId());
        assertEquals(TaskStatus.DONE, service.complete(created.getId()).getStatus());
        assertEquals(TaskStatus.DONE, service.get(created.getId()).getStatus());
    }

    @Test
    void cancellationPreventsCompletion() {
        Task created = service.create("task");
        assertEquals(TaskStatus.CANCELLED, service.cancel(created.getId()).getStatus());
        assertThrows(IllegalStateException.class, () -> service.complete(created.getId()));
    }

    @Test
    void missingTasksStayMissing() {
        UUID missing = UUID.randomUUID();
        assertThrows(TaskNotFoundException.class, () -> service.get(missing));
        assertThrows(TaskNotFoundException.class, () -> service.complete(missing));
        assertThrows(TaskNotFoundException.class, () -> service.cancel(missing));
    }

    @Test
    void rejectsNullDependenciesAndIds() {
        assertThrows(NullPointerException.class, () -> new TaskService(null));
        assertThrows(NullPointerException.class, () -> service.get(null));
        assertThrows(NullPointerException.class, () -> service.complete(null));
        assertThrows(NullPointerException.class, () -> service.cancel(null));
    }

    @Test
    void retainsLegacyPublicFieldContract() {
        assertEquals("demo", new LegacyCustomerRow("demo").customer_name);
    }
}
