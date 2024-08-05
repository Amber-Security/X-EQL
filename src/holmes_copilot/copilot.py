from typing import Set, List, Dict, Any


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
        head = default_rule_name + ": sequence "
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
            tag_meet = set()
            for f in fields:
                holmes_tag, field_name = f.split('@')
                if holmes_tag in tag_meet: continue
                tag_meet.add(holmes_tag)
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
    pass
