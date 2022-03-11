from termcolor import colored


FILENAME = "table.tex"


def detect_float(inputString):
    """
    detects index and lengths of float numbers in line)
    """
    float_poses = []
    cur_is_float = False
    start = None
    for i, e in enumerate(inputString):
        if e in [str(i) for i in range(10)] + ['.']:
            if not cur_is_float:
                cur_is_float = True
                start = i
        else:
            if cur_is_float:
                cur_is_float = False
                if i-start > 1:
                    float_poses.append((start, i-start))
    return float_poses


file = open(FILENAME, "r")
lines = file.read().splitlines()
new_lines = []
for line in lines:
    float_poses = detect_float(line)
    if float_poses:
        elems = []
        for float_pos in float_poses:
            start, len = float_pos
            elems.append(line[start: start+len])
        for elem in elems:
            line = line.replace(elem, f"{float(elem)*100:.1f}")
        print(colored(line, "green"))
    else:
        print(line)
    new_lines.append(line)


ans = input("\n\n Do you want to save the modifications?")
if ans[0].lower() == "y":
    file = open(FILENAME, "w")
    file.write("\n".join(new_lines))
    print(colored("Successfully changed modifications", "green"))
