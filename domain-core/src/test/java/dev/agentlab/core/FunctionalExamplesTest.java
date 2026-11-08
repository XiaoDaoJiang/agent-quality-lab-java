package dev.agentlab.core;

import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.stream.Collectors;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class FunctionalExamplesTest {
    @Test
    void filtersNormalizesAndSortsDistinctNames() {
        List<String> names = Arrays.asList(" Alice ", "bob", "ALICE", "", "Carol");
        Predicate<String> hasText = name -> !name.trim().isEmpty();
        Function<String, String> normalize = name -> name.trim().toLowerCase(java.util.Locale.ROOT);

        List<String> result = names.stream().filter(hasText).map(normalize).distinct().sorted(Comparator.naturalOrder())
            .collect(Collectors.toList());

        assertEquals(Arrays.asList("alice", "bob", "carol"), result);
    }

    @Test
    void groupsAndCountsWordsAcrossBatches() {
        List<List<String>> batches =
            Arrays.asList(Arrays.asList("java", "stream"), Arrays.asList("java", "function"), Collections.emptyList());

        Map<String, Long> counts = batches.stream().flatMap(List::stream)
            .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));

        assertEquals(Long.valueOf(2), counts.get("java"));
        assertEquals(Long.valueOf(1), counts.get("stream"));
        assertEquals(Long.valueOf(1), counts.get("function"));
        assertEquals(3, counts.size());
    }

    @Test
    void composesPredicatesAndHandlesMissingValues() {
        Predicate<String> nonEmpty = value -> !value.isEmpty();
        Predicate<String> longEnough = value -> value.length() >= 3;
        Predicate<String> accepted = nonEmpty.and(longEnough);
        Function<String, String> normalize = String::trim;

        Optional<String> found =
            Arrays.asList(" ", "ab", "  java  ").stream().map(normalize).filter(accepted).findFirst();
        Optional<String> missing = Collections.<String>emptyList().stream().filter(accepted).findFirst();

        assertEquals("java", found.orElse("unknown"));
        assertFalse(missing.isPresent());
        assertEquals("unknown", missing.orElse("unknown"));
    }

    @Test
    void mergesDuplicateKeysAndPartitionsValues() {
        List<String> items = Arrays.asList("a:2", "b:1", "a:3");
        BiFunction<Integer, Integer, Integer> add = Integer::sum;

        Map<String, Integer> totals = items.stream().map(item -> item.split(":"))
            .collect(Collectors.toMap(parts -> parts[0], parts -> Integer.valueOf(parts[1]), add::apply));
        Map<Boolean, List<Integer>> partitioned =
            totals.values().stream().collect(Collectors.partitioningBy(value -> value >= 3));

        assertEquals(Integer.valueOf(5), totals.get("a"));
        assertEquals(Integer.valueOf(1), totals.get("b"));
        assertTrue(partitioned.get(true).contains(5));
        assertEquals(Collections.singletonList(1), partitioned.get(false));
    }
}
