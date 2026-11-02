from cptextract.load_files import CPT_import


def consolidate_class_data(auto_delete):
    CPT_unique = set()
    dict2 = {}
    i_to_delete = []
    for i in range(len(CPT_import.all)):
        IDkey = CPT_import.all[i].CPT_ID
        x = CPT_import.all[i]
        if IDkey not in CPT_unique:
            dict2[IDkey] = x
            CPT_unique.add(IDkey)
        else:
            if x.file_extension == ".ags":
                dict2[IDkey] = x
            else:
                if auto_delete:
                    i_to_delete.append(CPT_import.all[i])
                else:
                    msg = f"\n{x.CPT_ID} {x.file_extension} not imported!"
                    x.add_msg(msg=msg, msg_type="e")
                pass
    for j in range(len(i_to_delete)):
        for i in range(len(CPT_import.all)):
            if CPT_import.all[i] == i_to_delete[j]:
                del CPT_import.all[i]
                break
    if len(CPT_import.all) == len(dict2.keys()):
        print(f"{len(i_to_delete)} duplicates removed")
        print(f"{len(CPT_import.all)} unique CPTs available for import!")
    else:
        print("Duplicates have not been removed. Class instances may not match dictionary")
    return dict2
