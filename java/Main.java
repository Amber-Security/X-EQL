import com.amber.holmes.Engine;
import com.amber.holmes.RuleLoader;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import java.io.File;
import java.io.IOException;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        ObjectMapper mapper = new ObjectMapper();

        try {
            // Read JSON files
            Object[] ast1 = (Object[]) mapper.readValue(new File("ast1.json"), new TypeReference<ArrayList<Object>>() {}).toArray();

            Engine engine = new Engine();
            engine.addHolmesRule(RuleLoader.loadRule(ast1));

            List<Map<String, Object>> testEventsWithoutNoise = new ArrayList<>();

            Map<String, Object> event1 = new HashMap<>();
            event1.put("holmes-tag", "ssh_login");
            event1.put("pid", "111");
            event1.put("sessionid", "aaaa");
            event1.put("localip", "10.2.3.4");
            event1.put("remoteip", "c");
            event1.put("f4", "d");
            event1.put("f5", "e");
            event1.put("time", 1);
            testEventsWithoutNoise.add(event1);

            Map<String, Object> event2 = new HashMap<>();
            event2.put("holmes-tag", "ssh_login");
            event2.put("pid", "112");
            event2.put("sessionid", "9876");
            event2.put("localip", "10.2.3.4");
            event2.put("remoteip", "10.2.3.9");
            event2.put("f4", " ");
            event2.put("f5", "x");
            event2.put("time", 10);
            testEventsWithoutNoise.add(event2);

            Map<String, Object> event3 = new HashMap<>();
            event3.put("holmes-tag", "tag2-----");
            event3.put("pid", "111");
            event3.put("sessionid", "dddd");
            event3.put("localip", "10.2.3.4");
            event3.put("remoteip", "c");
            event3.put("f4", " ");
            event3.put("f5", "y");
            event3.put("time", 11);
            testEventsWithoutNoise.add(event3);

            Map<String, Object> event4 = new HashMap<>();
            event4.put("holmes-tag", "read_knownhost");
            event4.put("pid", "112");
            event4.put("sessionid", "9876");
            event4.put("localip", "10.2.3.4");
            event4.put("remoteip", "10.2.3.9");
            event4.put("f4", " ");
            event4.put("f5", "x");
            event4.put("time", 12);
            testEventsWithoutNoise.add(event4);

            Map<String, Object> event5 = new HashMap<>();
            event5.put("holmes-tag", "tag3----------");
            event5.put("pid", "113");
            event5.put("sessionid", "eeee");
            event5.put("localip", "d");
            event5.put("remoteip", "a");
            event5.put("f4", "b");
            event5.put("f5", "y");
            event5.put("time", 20);
            testEventsWithoutNoise.add(event5);

            Map<String, Object> event6 = new HashMap<>();
            event6.put("holmes-tag", "ssh_login");
            event6.put("pid", "114");
            event6.put("sessionid", "eeee");
            event6.put("localip", "10.2.3.5");
            event6.put("remoteip", "10.2.3.9");
            event6.put("f4", "b");
            event6.put("f5", "x");
            event6.put("time", 21);
            testEventsWithoutNoise.add(event6);

            Map<String, Object> event7 = new HashMap<>();
            event7.put("holmes-tag", "ssh_login");
            event7.put("pid", "111");
            event7.put("sessionid", "3398");
            event7.put("localip", "10.2.3.5");
            event7.put("remoteip", "10.2.3.4");
            event7.put("f4", "b");
            event7.put("f5", "y");
            event7.put("time", 22);
            testEventsWithoutNoise.add(event7);

            long startTime = System.currentTimeMillis();
            while (true) {
                engine = new Engine();
                engine.addHolmesRule(RuleLoader.loadRule(ast1));
                for (Map<String, Object> event : testEventsWithoutNoise) {
                    engine.processEvent(event);
                }
            }

            /*
             * long endTime = System.currentTimeMillis();
             * 
             * // 计算并打印耗时
             * long duration = endTime - startTime;
             * System.out.println("任务耗时：" + duration + " 毫秒");
             * for (Map<String, Object> r : engine.fetchResults()) {
             * List<Map<String, Object>> output = (List<Map<String, Object>>)
             * r.get("output");
             * System.out.println(output.stream()
             * .map(m -> "(" + m.get("holmes-tag") + ", " + m.get("time") + ")")
             * .collect(java.util.stream.Collectors.toList()));
             * }
             */

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
