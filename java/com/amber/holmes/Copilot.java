package com.amber.holmes;


import java.util.*;

public class Copilot {
    public Copilot() {
    }

    public static String generateRule(List<Map<String, Object>> events) {
        Map<String, String> repeatedTagCache = new HashMap<>();
        List<String> lines = new ArrayList<>();
        List<String> tagSeq = new ArrayList<>();
        
        for (Map<String, Object> event : events) {
            String holmesTag = (String) event.get("holmes-tag");
            repeatedTagCache.putIfAbsent(holmesTag, holmesTag);
            repeatedTagCache.put(holmesTag, repeatedTagCache.get(holmesTag) + "#");
            holmesTag = repeatedTagCache.get(holmesTag);
            tagSeq.add(holmesTag);
        }
        
        String defaultRuleName = String.join("_TO_", tagSeq).replace("#", "");
        String head = defaultRuleName + ": sequence ";
        repeatedTagCache.clear();
        
        // calc
        Map<Object, Set<String>> value2fields = new HashMap<>();
        for (Map<String, Object> event : events) {
            String holmesTag = (String) event.get("holmes-tag");
            repeatedTagCache.putIfAbsent(holmesTag, holmesTag);
            repeatedTagCache.put(holmesTag, repeatedTagCache.get(holmesTag) + "#");
            holmesTag = repeatedTagCache.get(holmesTag);
            
            for (Map.Entry<String, Object> entry : event.entrySet()) {
                String fieldName = entry.getKey();
                if (fieldName.equals("holmes-tag")) continue;
                Object fieldValue = entry.getValue();
                value2fields.putIfAbsent(fieldValue, new HashSet<>());
                value2fields.get(fieldValue).add(holmesTag + "@" + fieldName);
            }
        }
        
        // generate groups
        Map<String, List<AbstractMap.SimpleEntry<String, String>>> eventGroups = new HashMap<>();
        int i = 0;
        for (Object v : value2fields.keySet()) {
            Set<String> fields = value2fields.get(v);
            String gid = "g" + i;
            if (fields.stream().map(f -> f.split("@")[0]).distinct().count() == 1) continue;
            Set<String> tagMeet = new HashSet<>();
            for (String f : fields) {
                String[] parts = f.split("@");
                String holmesTag = parts[0];
                String fieldName = parts[1];
                if (tagMeet.contains(holmesTag)) continue;
                tagMeet.add(holmesTag);
                eventGroups.putIfAbsent(holmesTag, new ArrayList<>());
                eventGroups.get(holmesTag).add(new AbstractMap.SimpleEntry<>(gid, fieldName));
            }
            i++;
        }
        
        // for
        for (String tag : tagSeq) {
            if (!eventGroups.containsKey(tag)) {
                lines.add("\t[" + tag.replace("#", "") + "]");
                continue;
            }
            List<AbstractMap.SimpleEntry<String, String>> groups = eventGroups.get(tag);
            String constraint = groups.stream()
                .map(entry -> "(" + entry.getValue() + "):" + entry.getKey())
                .collect(java.util.stream.Collectors.joining(", "));
            lines.add("\t[" + tag.replace("#", "") + "] by " + constraint);
        }
        lines.add(0, head);
        return String.join("\n", lines);
    }

    public static void main(String[] args) {
    }
}

