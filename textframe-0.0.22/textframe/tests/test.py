import textframe as tf


new_frame = tf.TextFrame()

column_list1 = [{"key": "Key One", "width": 30}, {"key": "Key Two"}, {"key": "Key Three", "width": 20}]

row_list1 = [
    {"Key One": "Row One Column One", "Key Two": "Row One Column Two", "Key Three": "Row One Column Three"},
    {"Key One": "Row Two Column Two", "Key Two": "Row Two Column Two", "Key Three": "Row Two Column Three"},
    {"Key One": "Row Three Column One", "Key Two": "Row Three Column Two", "Key Three": "Row Three Column Three"},
]

new_frame.add_table_frame(column_list1, row_list1)
new_frame.print()


column_list2 = [
    {"key": "Key One", "width": "50%", "divider": "thick"},
    {"key": "Key Two", "align": "right"},
    {"key": "Key Three", "align": "right"},
]

row_list2 = [
    {"Key One": "Some string value", "Key Two": 4, "Key Three": 9.6},
    {"Key One": "Some other string value", "Key Two": 5, "Key Three": 4.6},
    {"Key One": "Some final string value", "Key Two": 100, "Key Three": 328.832},
]

new_frame.add_text_frame("Default text")


new_frame.add_text_frame("Example text frame with left indentation", multiline=False, text_align="left")
new_frame.add_text_frame("Example text frame with center indentation", multiline=False, text_align="center")
new_frame.add_text_frame("Example text frame with right indentation", multiline=False, text_align="right")

new_frame.add_text_frame(666)


really_long_string = "Commodo elit at imperdiet dui accumsan sit amet nulla. Sodales neque sodales ut etiam sit amet nisl purus. Convallis posuere morbi leo urna molestie at elementum. Enim nunc faucibus a pellentesque sit amet porttitor. Enim nulla aliquet porttitor lacus luctus accumsan tortor. Ullamcorper velit sed ullamcorper morbi. Sit amet porttitor eget dolor morbi non arcu. Eget mauris pharetra et ultrices neque ornare aenean euismod elementum. Euismod lacinia at quis risus sed vulputate odio. Varius quam quisque id diam. Habitant morbi tristique senectus et netus et malesuada fames ac. Ornare quam viverra orci sagittis eu volutpat odio. Nisl suscipit adipiscing bibendum est ultricies. Adipiscing elit pellentesque habitant morbi tristique senectus. Tellus cras adipiscing enim eu turpis egestas pretium aenean pharetra. At consectetur lorem donec massa sapien faucibus et molestie. Neque ornare aenean euismod elementum nisi quis eleifend quam. A arcu cursus vitae congue mauris."

new_frame.add_text_frame(really_long_string, multiline=False)
new_frame.add_text_frame(really_long_string, max_lines=3)

new_frame.add_text_frame(really_long_string)

new_frame.add_table_frame(column_list2, row_list2)

column_list3 = [
    {
        "string": "Quam elementum pulvinar etiam non quam lacus suspendisse faucibus. Enim nec dui nunc mattis enim ut tellus. Est placerat in egestas erat imperdiet sed euismod nisi porta. At tempor commodo ullamcorper a lacus vestibulum sed. Porta nibh venenatis cras sed. Cras sed felis eget velit aliquet sagittis id consectetur. Aliquam id diam maecenas ultricies mi. ",
        "width": 40,
        "divider": "thick",
    },
    {
        "string": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    },
    {
        "string": "Commodo elit at imperdiet dui accumsan sit amet nulla. Sodales neque sodales ut etiam sit amet nisl purus. Convallis posuere morbi leo urna molestie at elementum. Enim nunc faucibus a pellentesque sit amet porttitor. Enim nulla aliquet porttitor lacus luctus accumsan tortor. Ullamcorper velit sed ullamcorper morbi. Sit amet porttitor eget dolor morbi non arcu. Eget mauris pharetra et ultrices neque ornare aenean euismod elementum. Euismod lacinia at quis risus sed vulputate odio. Varius quam quisque id diam. Habitant morbi tristique senectus et netus et malesuada fames ac. Ornare quam viverra orci sagittis eu volutpat odio. Nisl suscipit adipiscing bibendum est ultricies. Adipiscing elit pellentesque habitant morbi tristique senectus. Tellus cras adipiscing enim eu turpis egestas pretium aenean pharetra. At consectetur lorem donec massa sapien faucibus et molestie. Neque ornare aenean euismod elementum nisi quis eleifend quam. A arcu cursus vitae congue mauris."
    },
]

column_list4 = [
    {
        "string": "Quam elementum pulvinar etiam non quam lacus suspendisse faucibus. Enim nec dui nunc mattis enim ut tellus. Est placerat in egestas erat imperdiet sed euismod nisi porta. At tempor commodo ullamcorper a lacus vestibulum sed. Porta nibh venenatis cras sed. Cras sed felis eget velit aliquet sagittis id consectetur. Aliquam id diam maecenas ultricies mi. ",
        "width": 20,
    },
    {
        "string": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "divider": "thick",
    },
    {
        "string": "Commodo elit at imperdiet dui accumsan sit amet nulla. Sodales neque sodales ut etiam sit amet nisl purus. Convallis posuere morbi leo urna molestie at elementum. Enim nunc faucibus a pellentesque sit amet porttitor. Enim nulla aliquet porttitor lacus luctus accumsan tortor. Ullamcorper velit sed ullamcorper morbi. Sit amet porttitor eget dolor morbi non arcu. Eget mauris pharetra et ultrices neque ornare aenean euismod elementum. Euismod lacinia at quis risus sed vulputate odio. Varius quam quisque id diam. Habitant morbi tristique senectus et netus et malesuada fames ac. Ornare quam viverra orci sagittis eu volutpat odio. Nisl suscipit adipiscing bibendum est ultricies. Adipiscing elit pellentesque habitant morbi tristique senectus. Tellus cras adipiscing enim eu turpis egestas pretium aenean pharetra. At consectetur lorem donec massa sapien faucibus et molestie. Neque ornare aenean euismod elementum nisi quis eleifend quam. A arcu cursus vitae congue mauris."
    },
]

column_list5 = [
    {"string": 123, "width": "20%", "divider": "thick"},
    {
        "string": 456,
    },
    {"string": 789, "width": "25%"},
]

new_frame.add_grid_frame(column_list3, max_lines=1)
new_frame.add_grid_frame(column_list4, max_lines=6)
new_frame.add_grid_frame(column_list4)
new_frame.add_grid_frame(column_list5)

new_frame.print()
