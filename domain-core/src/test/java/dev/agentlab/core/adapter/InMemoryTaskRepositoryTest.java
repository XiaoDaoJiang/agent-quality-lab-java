package dev.agentlab.core.adapter;

import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;

import dev.agentlab.core.domain.Task;
import dev.agentlab.core.domain.TaskStatus;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class InMemoryTaskRepositoryTest {
    @Test
    void rejectsDuplicatesAndInvalidTransitionsWithoutLosingExistingTask() {
        InMemoryTaskRepository repository = new InMemoryTaskRepository();
        Task task = Task.create(UUID.randomUUID(), "task");
        repository.insert(task);
        assertThrows(IllegalStateException.class, () -> repository.insert(task));
        assertThrows(NullPointerException.class, () -> repository.update(task.getId(), old -> null));
        assertThrows(IllegalArgumentException.class,
            () -> repository.update(task.getId(), old -> Task.create(UUID.randomUUID(), "different")));
        assertEquals(TaskStatus.TODO, repository.find(task.getId()).get().getStatus());
    }

    @Test
    void terminalTransitionsAreAtomicUnderContention() throws Exception {
        InMemoryTaskRepository repository = new InMemoryTaskRepository();
        Task task = Task.create(UUID.randomUUID(), "task");
        repository.insert(task);
        ThreadPoolExecutor executor = new ThreadPoolExecutor(2, 2, 0, TimeUnit.SECONDS, new LinkedBlockingQueue<>(2));
        try {
            Callable<Boolean> complete = () -> attempt(() -> repository.update(task.getId(), Task::complete));
            Callable<Boolean> cancel = () -> attempt(() -> repository.update(task.getId(), Task::cancel));
            Future<Boolean> first = executor.submit(complete);
            Future<Boolean> second = executor.submit(cancel);
            assertTrue(first.get(5, TimeUnit.SECONDS) ^ second.get(5, TimeUnit.SECONDS));
        } finally {
            executor.shutdownNow();
            assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS));
        }
    }

    private static boolean attempt(Runnable transition) {
        try {
            transition.run();
            return true;
        } catch (IllegalStateException expectedConflict) {
            return false;
        }
    }
}
