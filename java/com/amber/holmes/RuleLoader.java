package com.amber.holmes;

import java.util.List;
import java.util.ArrayList;

class KeyGroupBind {
    public String groupId;
    List<String> fields;

    public KeyGroupBind(String groupId, List<String> fields) {
        this.groupId = groupId;
        this.fields = fields;
    }
}

class TagRule {
    public String id;

    public TagRule(String id) {
        this.id = id;
    }
}

class TagNode {
    public TagRule tagRule;
    public Integer denseGid;
    public List<KeyGroupBind> binders;

    public TagNode(TagRule tagRule, List<KeyGroupBind> binders, Integer denseGid) {
        this.tagRule = tagRule;
        this.denseGid = denseGid;
        this.binders = binders;
    }
}

class HolmesRule {
    public String ruleId;
    public String shape;
    public List<TagNode> tagNodes;
    public int maxSpan;

    public HolmesRule(String ruleId, String shape, List<TagNode> tagNodes, int maxSpan) {
        this.ruleId = ruleId;
        this.shape = shape;
        this.tagNodes = tagNodes;
        this.maxSpan = maxSpan;
    }
}

public class RuleLoader {
    public static TagNode genTagNode(Object[] eventRule, List<KeyGroupBind> commonBinder, Integer denseGid) {
        String tid = (String) eventRule[1];
        TagRule tagRule = new TagRule(tid);
        List<KeyGroupBind> binders = new ArrayList<>(commonBinder);
        if (eventRule.length == 3) {
            Object[] binderData = (Object[]) ((ArrayList) eventRule[2]).toArray();
            for (Object _data : binderData) {
                Object[] data = ((ArrayList) _data).toArray();
                binders.add(new KeyGroupBind((String) data[0], (List<String>) data[1]));
            }
        }
        return new TagNode(tagRule, binders, denseGid);
    }

    public static HolmesRule loadRule(Object[] ast) {
        Object[] head = (Object[]) ((ArrayList) ast[1]).toArray();
        Object[] seq = (Object[]) ((ArrayList) ast[2]).toArray();
        String ruleId, shape;
        List<KeyGroupBind> commonBinder = new ArrayList<>();

        if (head.length == 4) {
            ruleId = (String) head[1];
            shape = (String) head[2];
            List<String> commonk = (List<String>) ((Object[]) head[3])[1];
            commonBinder.add(new KeyGroupBind("*", commonk));
        } else {
            ruleId = (String) head[1];
            shape = (String) head[2];
        }

        List<TagNode> tagNodes = new ArrayList<>();
        int denseGid = 0;
        for (Object block : seq) {
            if (((ArrayList) block).get(0) instanceof String) {
                tagNodes.add(genTagNode((Object[]) ((ArrayList) block).toArray(), commonBinder, null));
            } else {
                for (Object eventRule : (Object[]) ((ArrayList) block).toArray()) {
                    System.out.println(eventRule);
                    tagNodes.add(genTagNode((Object[]) eventRule, commonBinder, denseGid));
                }
                denseGid++;
            }
        }

        return new HolmesRule(ruleId, shape, tagNodes, 60);
    }
}
