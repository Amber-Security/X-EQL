from typing import Set, List, Dict, Any

from holmes_rule.parser import Parser


class Copilot:
    def __init__(self) -> None:
        pass

    def generate_rule(events:List[Dict]) -> str:
        repeated_tag_cache = {}
        lines = []
        tag_seq = []
        for event in events:
            holmes_tag = event["holmes-tag"]
            if holmes_tag not in repeated_tag_cache: repeated_tag_cache[holmes_tag] = holmes_tag
            repeated_tag_cache[holmes_tag] += '#'
            holmes_tag = repeated_tag_cache[holmes_tag]
            tag_seq.append(holmes_tag)
        default_rule_name = "_TO_".join(tag_seq).replace("#", "")
        head = default_rule_name + ": sparse sequence "
        repeated_tag_cache = {}
        # calc
        value2fields:Dict[Any, Set[str]] = {}
        for event in events:
            holmes_tag = event["holmes-tag"]
            if holmes_tag not in repeated_tag_cache: repeated_tag_cache[holmes_tag] = holmes_tag
            repeated_tag_cache[holmes_tag] += '#'
            holmes_tag = repeated_tag_cache[holmes_tag]
            for field_name in event:
                if field_name == "holmes-tag": continue
                field_value = event[field_name]
                if field_value not in value2fields: value2fields[field_value] = set()
                value2fields[field_value].add('@'.join([holmes_tag, field_name]))
        # generate groups
        event_groups:Dict[str, List] = {}
        for i, v in enumerate(value2fields):
            # gen one group
            fields = value2fields[v]
            gid = 'g' + str(i)
            if len(set([f.split('@')[0] for f in fields])) == 1: continue
            for f in fields:
                holmes_tag, field_name = f.split('@')
                if holmes_tag not in event_groups: event_groups[holmes_tag] = []
                event_groups[holmes_tag].append((gid, field_name))
        # for
        for tag in tag_seq:
            if tag not in event_groups:
                lines.append('\t[' + tag.replace("#", "") + ']')
                continue
            groups = event_groups[tag]
            constraint = ', '.join(['(' + f + '):' + gid for gid, f in groups])
            lines.append('\t[' + tag.replace("#", "") + '] by ' + constraint)
        lines.insert(0, head)
        return '\n'.join(lines)

if __name__ == "__main__":
    test_events_without_noise2 = [
        {"holmes-tag": "tag1", "pid": 111, "f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e", "time": 1},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "y", "time": 11},
        {"holmes-tag": "tag2", "pid": 111, "f1": "d", "f2": "e", "f3": "c", "f4": " ", "f5": "x", "time": 12},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 20},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "x", "time": 21},
        {"holmes-tag": "tag3", "pid": 111, "f1": "e", "f2": "d", "f3": "a", "f4": "b", "f5": "y", "time": 22},
    ]
    test_events_without_noise = [
        {"holmes-tag": "ssh_login", "pid": 112, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": " ", "f5": "x", "time": 10},
        {"holmes-tag": "read_knownhost", "pid": 113, "sessionid": "9876", "localip": "10.2.3.4", "remoteip": "10.2.3.9", "f4": "-", "f5": "z", "time": 12},
        {"holmes-tag": "ssh_login", "pid": 111, "sessionid": "3398", "localip": "10.2.3.5", "remoteip": "10.2.3.4", "f4": "b", "f5": "y", "time": 22},
    ]
    rule = Copilot.generate_rule(test_events_without_noise)
    print(rule)
