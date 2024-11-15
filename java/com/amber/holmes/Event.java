package com.amber.holmes;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

class Event {
    public String eid;
    public Map<String, Object> rawEvent;
    public String tidDyn;
    public Map<String, List<String>> kgIncMap;
    public Map<String, Object[]> kgInc;

    public Event(String eid, Map<String, Object> rawEvent, String tidDyn, Map<String, List<String>> kgIncMap) {
        this.eid = eid;
        this.rawEvent = rawEvent;
        this.tidDyn = tidDyn;
        this.kgIncMap = kgIncMap;
        this.kgInc = new HashMap<>();
        genKgInc();
    }

    private void genKgInc() {
        if (kgIncMap == null) {
            assert "DENSE_BOOT".equals(tidDyn);
            return;
        }
        for (Map.Entry<String, List<String>> entry : kgIncMap.entrySet()) {
            String groupId = entry.getKey();
            List<String> fields = entry.getValue();
            Object[] fieldValues = new Object[fields.size()];
            for (int i = 0; i < fields.size(); i++) {
                fieldValues[i] = rawEvent.get(fields.get(i));
            }
            kgInc.put(groupId, fieldValues);
        }
    }
}
