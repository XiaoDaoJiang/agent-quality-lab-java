package dev.agentlab.offline;

import java.io.DataInputStream;
import java.io.InputStream;
import java.util.UUID;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import dev.agentlab.core.adapter.InMemoryTaskRepository;
import dev.agentlab.core.application.TaskService;
import dev.agentlab.core.compat.LegacyCustomerRow;
import dev.agentlab.core.domain.Task;
import dev.agentlab.core.domain.TaskNotFoundException;
import dev.agentlab.core.domain.TaskStatus;

/** Dependency-free smoke check. It is not a replacement for JUnit, ArchUnit or HTTP tests. */
public final class DomainSmoke {
    private static int checks;

    private DomainSmoke() {
    }

    public static void main(String[] args) throws Exception {
        UUID id = UUID.randomUUID();
        Task task = Task.create(id, "  quality  ");
        check(task.getId().equals(id), "id preserved");
        check(task.getTitle().equals("quality"), "title normalized");
        check(task.getStatus() == TaskStatus.TODO, "initial status");
        fails(IllegalArgumentException.class, () -> Task.create(id, null));
        fails(IllegalArgumentException.class, () -> Task.create(id, " "));
        fails(NullPointerException.class, () -> Task.create(null, "task"));
        StringBuilder boundary = new StringBuilder();
        for (int index = 0; index < 120; index++) {
            boundary.append('a');
        }
        check(Task.create(id, boundary.toString()).getTitle().length() == 120, "title boundary");
        fails(IllegalArgumentException.class, () -> Task.create(id, boundary + "a"));
        Task done = task.complete();
        check(task.getStatus() == TaskStatus.TODO, "immutable original");
        check(done.getStatus() == TaskStatus.DONE, "completed");
        check(done.complete() == done, "completion idempotent");
        fails(IllegalStateException.class, done::cancel);
        Task cancelled = task.cancel();
        check(cancelled.cancel() == cancelled, "cancellation idempotent");
        fails(IllegalStateException.class, cancelled::complete);
        InMemoryTaskRepository repository = new InMemoryTaskRepository();
        TaskService service = new TaskService(repository);
        fails(NullPointerException.class, () -> new TaskService(null));
        fails(NullPointerException.class, () -> service.get(null));
        fails(NullPointerException.class, () -> service.complete(null));
        fails(NullPointerException.class, () -> service.cancel(null));
        fails(TaskNotFoundException.class, () -> service.get(UUID.randomUUID()));
        fails(TaskNotFoundException.class, () -> service.complete(UUID.randomUUID()));
        Task created = service.create("service");
        check(service.get(created.getId()).getTitle().equals("service"), "service read");
        check(service.complete(created.getId()).getStatus() == TaskStatus.DONE, "service completion");
        fails(IllegalStateException.class, () -> repository.insert(created));
        fails(NullPointerException.class, () -> repository.update(created.getId(), old -> null));
        fails(IllegalArgumentException.class,
                () -> repository.update(created.getId(), old -> Task.create(UUID.randomUUID(), "wrong id")));
        check(service.get(created.getId()).getStatus() == TaskStatus.DONE, "failed update is atomic");
        check(new LegacyCustomerRow("legacy").customer_name.equals("legacy"), "legacy contract");
        for (int iteration = 0; iteration < 25; iteration++) {
            concurrentTerminalTransition();
        }
        try (InputStream stream = Task.class.getResourceAsStream("Task.class")) {
            if (stream == null) {
                throw new AssertionError("Task.class resource missing");
            }
            try (DataInputStream input = new DataInputStream(stream)) {
                check(input.readInt() == 0xCAFEBABE, "class header");
                input.readUnsignedShort();
                check(input.readUnsignedShort() == 52, "Java 8 class-file target");
            }
        }
        System.out.println("DOMAIN SMOKE PASSED: " + checks + " assertions; runtime="
                + System.getProperty("java.version") + "; class target=52 (Java 8)");
    }

    private static void concurrentTerminalTransition() throws Exception {
        InMemoryTaskRepository repository = new InMemoryTaskRepository();
        Task task = Task.create(UUID.randomUUID(), "concurrent");
        repository.insert(task);
        ThreadPoolExecutor executor = new ThreadPoolExecutor(2, 2, 0, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(2));
        try {
            Future<Boolean> one = executor.submit(() -> attempt(() -> repository.update(task.getId(), Task::complete)));
            Future<Boolean> two = executor.submit(() -> attempt(() -> repository.update(task.getId(), Task::cancel)));
            check(one.get(5, TimeUnit.SECONDS) ^ two.get(5, TimeUnit.SECONDS), "one terminal transition wins");
        } finally {
            executor.shutdownNow();
            check(executor.awaitTermination(5, TimeUnit.SECONDS), "executor terminated");
        }
    }

    private static boolean attempt(Runnable operation) {
        try {
            operation.run();
            return true;
        } catch (IllegalStateException expected) {
            return false;
        }
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
        checks++;
    }

    private static void fails(Class<? extends Throwable> expected, Runnable operation) {
        try {
            operation.run();
        } catch (Throwable actual) {
            check(expected.isInstance(actual), "expected " + expected + ", got " + actual);
            return;
        }
        throw new AssertionError("Expected " + expected.getName());
    }
}
