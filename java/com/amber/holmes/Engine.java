package com.amber.holmes;

import java.util.*;

public class Engine {
    // For results caching, fetch by application layer with Engine.fetchResults()
    private List<Map<String, Object>> resultsCachedBuffer;
    // One worker is an engine instance corresponding to one rule
    private Map<String, Worker> workers;
    // Record which tags should be checked by which rules(workers). The value is a
    // set of worker IDs
    private Map<String, Set<String>> tagIndex;

    public Engine() {
        this.resultsCachedBuffer = new ArrayList<>();
        this.workers = new HashMap<>();
        this.tagIndex = new HashMap<>();
    }

    public String addHolmesRule(HolmesRule rule) {
        // check exist
        if (workers.containsKey(rule.ruleId)) {
            return "exist";
        }
        // add worker
        Worker worker = new Worker(rule, rule.ruleId);
        workers.put(rule.ruleId, worker);
        // add tag2worker index
        for (TagNode tagNode : rule.tagNodes) {
            String tagId = tagNode.tagRule.id;
            tagIndex.computeIfAbsent(tagId, k -> new HashSet<>()).add(rule.ruleId);
        }
        return "success";
    }

    public String delHolmesRule(String ruleId) {
        // check exist
        if (!workers.containsKey(ruleId)) {
            return "not exist";
        }
        // del worker
        workers.remove(ruleId);
        return "success";
    }

    public String updateHolmesRule(HolmesRule rule) {
        String result = delHolmesRule(rule.ruleId);
        if (result.equals("not exist"))
            return result;
        return addHolmesRule(rule);
    }

    public List<Map<String, Object>> fetchResults() {
        // will clean the cached results
        List<Map<String, Object>> results = new ArrayList<>(resultsCachedBuffer);
        resultsCachedBuffer.clear();
        return results;
    }

    public void processEvent(Map<String, Object> event) {
        String tagId = (String) event.get("holmes-tag");
        if (!tagIndex.containsKey(tagId))
            return;
        for (String holmesRuleId : tagIndex.get(tagId)) {
            Worker worker = workers.get(holmesRuleId);
            List<List<Object>> results = worker.processEvent(event);
            worker.prune((long) (Integer) event.get("time"));
            if (!results.isEmpty()) {
                for (List<Object> result : results) {
                    Map<String, Object> output = new HashMap<>();
                    output.put("rulename", worker.rulename);
                    output.put("output", result);
                    resultsCachedBuffer.add(output);
                }
            }
        }
    }
}
