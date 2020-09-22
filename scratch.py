import requests
import json
import os

import settings



class OuterClass():

    attribute = "attribute"

    def __init__(self):
        self.init_attribute = "init attribute"
        self.list = []

    def outer_method1(self):
        print("This is outer method 1")

    def outer_method2(self):
        print("This is outer method 2")

    def add_to_list(self, thing_to_add):
        self.list.append(thing_to_add)
        print(self.list)

    def add_inner(self):
        self.inner_container = OuterClass.InnerClass(self)
        # return OuterClass.InnerClass(self)



    class InnerClass():

        def __init__(self, outer_instance):
            self.outer = outer_instance
            self.inner_method_to_access_outer()

        def inner_method_to_access_outer(self):
            self.outer.add_to_list("Added from inner class")


        def inner_method1(self):
            print("This is inner method 1")



test = OuterClass()
test.add_inner()
test.inner_container.inner_method1()


print(test.__dict__)

# test.inner_container.inner_method1()



