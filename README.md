# dynamic-health-rule-pod
This script is built for create the health rule for Pods that spin up/down in the selected namespace. There's 2 health rule templates to be selected, one is the CPU Utilization Health Rule and the others is the Memory Usage Health Rule.

1. Python v3+
NOTE: If pip is not installed this is also required. (Typically pip is installed with Python.) NOTE: pip has different versions depending on your install. pip/pip3 may be required.

2. The tencentcloud-sdk-python must be installed
https://github.com/TencentCloud/tencentcloud-sdk-python

    pip3 install --upgrade tencentcloud-sdk-python

3. The "requests", "glom" and "datetime" library for Python must be installed/available.

    pip3 install requests
    
    pip3 install glom
