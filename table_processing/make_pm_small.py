import re

make_bold = True

filename = "table_results.tex"
final_tex = ""
with open(filename, 'r') as tex_file:
    for line in tex_file.readlines():
        if not "&" in line:
            final_tex += line
        else:
            newline = ""
            all_means = []
            for el in line.split("&"):
                if "\pm" in el:
                    mean, std = re.findall('[-+]?[0-9]+\.?[0-9]*', el)
                    all_means.append(float(mean))
                    if mean.startswith("-"):
                        newline += "\\text{-}"
                        mean = mean[1:]
                    if "bf" in el:
                        import ipdb; ipdb.set_trace()
                    newline += "$" + mean + "\\mbox{\\scriptsize$\\pm" + std + "$}$"
                else:
                    mean = re.findall('[-+]?[0-9]+\.?[0-9]*', el)
                    if len(mean) == 1 and "\\" not in el:
                        if "." in mean[0]:
                            all_means.append(float(mean[0]))
                        else:
                            all_means.append(int(mean[0]))
                    newline += el.replace(" ", "")
                newline += "  &  "
            if all_means:
                highest_score = max(all_means)
                position = newline.index(str(highest_score))
                if newline[position-1] == "$":
                    newline = newline.replace(str(highest_score), '\\mathbf{' + str(highest_score) + '}')
                else:
                    newline = newline.replace(str(highest_score), '$\\mathbf{' + str(highest_score) + '}$')
            # print(newline[:-5].count("&"), line.count("&"), line[:10])
            newline = newline[:-5]
            if line.endswith("\\\\\n") and not newline.endswith("\\\\\n"):
                newline += "\\\\\n"
            final_tex += newline

with open(f"corrected_{filename}", "w") as outfile:
    outfile.write(final_tex)
# \text{-}$20\mbox{\scriptsize$\pm 0.7$}$
