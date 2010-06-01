#scheduler
import MySQLdb
import DomainObjects
import statistics
from operator import itemgetter

#function that creates Domain objects - node, cpu and fan from the result of the sql query
def createNodes(r):
	numRows = r.num_rows()
	print  "\nNumber of Rows = ",numRows
	print "\nNumber of Columns = ",r.num_fields()

	tupleDict = {}
	#creating a dictionary of the returned results
	for i in range(1,numRows+1):

        	#first param - no.of rows, second parameter is made 2 to store row as a dict
        	row= r.fetch_row(1,2)
        	#print row

        	#check if no nodes have been added for this node id, key is the node id, value is a list of dictionaries (one for ea$
        	if(tupleDict.has_key(int(row[0]["qosMain_1.nId"]))):
                	tupleDict[int(row[0]["qosMain_1.nId"])].append(row[0])
		else:
                	rowList = [row[0]]
                	tupleDict[int(row[0]["qosMain_1.nId"])] = rowList

	nodeList = []
	
	#printing the different node details    
	for k,v in tupleDict.items():
        	print "Node id = %d, nodes = %s" % (k,v)
        	print "\n\n\n"
		#v[0] itself is a dict for the very first appearance of the node
		nodeMemUsage = float(v[0]["qosMain_1.memUsage"].split("/")[0])+float(v[0]["qosMain_1.memUsage"].split("/")[1])
		
		nwSRusageArr = v[0]["qosMain_1.nwSRUsage"].split("/")

		nwSRUsage = 0
                nnc = 0
                itr = 0
		for nwSR in nwSRusageArr:
			nwSRUsage += float(nwSR)
			if(itr%2==0):
				nnc+=1
			itr+=1
		#nwSRUsage/=nnc   
		nodeObject = DomainObjects.Node(k,float(v[0]["qosMain_1.powerUsage"]),nodeMemUsage,nwSRUsage,v[0]["qosMain_1.status"],float(v[0]["qosMain_1.performance"]))
		
		cpuDict = {}
		fanDict = {}

		for tuple in v:
			if(not cpuDict.has_key(tuple["nodeCpus_1.cpuId"])):
				cpuObject = DomainObjects.CPU(k,tuple["nodeCpus_1.cpuId"],tuple["nodeCpus_1.cpuName"],float(tuple["nodeCpus_1.cpuTemp"]),float(tuple["nodeCpus_1.cpuLoad"]),float(tuple["nodeCpus_1.cpuSpeed"]),tuple["nodeCpus_1.cpuType"],float(tuple["nodeCpus_1.cpuCache"]),tuple["nodeCpus_1.cpuState"])		
				cpuDict[tuple["nodeCpus_1.cpuId"]] = cpuObject

			if(not fanDict.has_key(tuple["nodeFans_1.fanId"])):
                                fanObject = DomainObjects.Fan(k,tuple["nodeFans_1.fanId"],tuple["nodeFans_1.fanName"],float(tuple["nodeFans_1.fanspeed"]),tuple["nodeFans_1.state"])
				fanDict[tuple["nodeFans_1.fanId"]] = fanObject

		nodeObject.setCpuAndFans(cpuDict.values(),fanDict.values())
		nodeObject.setNetCpuParamsForNode()
		nodeObject.setNetFanParamsForNode()
		nodeList.append(nodeObject)

	return nodeList

#End of function

#function to read weight from the files
def getWeights(filename):
	infile = file(filename,'r')
	map = {}
	for line in infile.readlines():
		map[line.split(":")[0]] = int(line.split(":")[1])
	infile.close()
	return map

#function to get node weights
def getNodeWeights(nodeList,pw,gw):
	nodePowerUsageList = []
	nodeMemUsageList = []
	nodeNwSRUsageList = []
	nodePerformanceList = []
	nodeNetNodeTempList = []
	nodeNetNodeLoadList = []
	nodeNetNodeSpeedList = []
	nodeNetNodeCacheList = []
	nodeNetNodeFanSpeedList = []

	for node in nodeList:
		nodePowerUsageList.append(node.powerUsage*-1)
		nodeMemUsageList.append(node.memUsage*-1)
		nodeNwSRUsageList.append(node.nwSRUsage*-1)
		nodePerformanceList.append(node.performance)
		nodeNetNodeTempList.append(node.netNodeTemp*-1)
		nodeNetNodeLoadList.append(node.netNodeLoad*-1)
		nodeNetNodeSpeedList.append(node.netNodeSpeed)
		nodeNetNodeCacheList.append(node.netNodeCache)
		nodeNetNodeFanSpeedList.append(node.netNodeFanSpeed*-1)

	nodePowerUsageGrade = statistics.stat.histogram(nodePowerUsageList,len(gw.values()))
	print nodePowerUsageGrade

	nodeMemUsageGrade = statistics.stat.histogram(nodeMemUsageList,len(gw.values()))
        print nodeMemUsageGrade

	nodeNwSRUsageGrade = statistics.stat.histogram(nodeNwSRUsageList,len(gw.values()))
        print nodeNwSRUsageGrade

	nodePerformanceGrade = statistics.stat.histogram(nodePerformanceList,len(gw.values()))
        print nodePerformanceGrade

	nodeNetNodeTempGrade = statistics.stat.histogram(nodeNetNodeTempList,len(gw.values()))
        print nodeNetNodeTempGrade

	nodeNetNodeLoadGrade = statistics.stat.histogram(nodeNetNodeLoadList,len(gw.values()))
        print nodeNetNodeLoadGrade

	nodeNetNodeSpeedGrade = statistics.stat.histogram(nodeNetNodeSpeedList,len(gw.values()))
        print nodeNetNodeSpeedGrade

	nodeNetNodeCacheGrade = statistics.stat.histogram(nodeNetNodeCacheList,len(gw.values()))
        print nodeNetNodeCacheGrade

	nodeNetFanSpeedGrade = statistics.stat.histogram(nodeNetNodeFanSpeedList,len(gw.values()))
        print nodeNetFanSpeedGrade

	nodeWeight = {}
	netPw = 0
	for node in nodeList:
		if(netPw==0):
			netPw += pw['powerUsage']+pw['memUsage']+pw['nwSRUsage']+pw['performance']+pw['cpuTemp']+pw['cpuLoad']+pw['cpuSpeed']+pw['cpuCache']+pw['fanSpeed']
		nw = 0
		nw +=nodePowerUsageGrade[node.powerUsage*-1]*pw['powerUsage']
		nw +=nodeMemUsageGrade[node.memUsage*-1]*pw['memUsage']
		nw +=nodeNwSRUsageGrade[node.nwSRUsage*-1]*pw['nwSRUsage']
                nw +=nodePerformanceGrade[node.performance]*pw['performance']
		nw +=nodeNetNodeTempGrade[node.netNodeTemp*-1]*pw['cpuTemp']
                nw +=nodeNetNodeLoadGrade[node.netNodeLoad*-1]*pw['cpuLoad']
		nw +=nodeNetNodeSpeedGrade[node.netNodeSpeed]*pw['cpuSpeed']
                nw +=nodeNetNodeCacheGrade[node.netNodeCache]*pw['cpuCache']
	
		print "\nNodeWeight = "+str(nw) 
		print "nNetPw = "+str(netPw)

                nw = float(nw)/float(netPw) #calculating on a cpu basis
		nw = (float(nw) + float(nodeNetFanSpeedGrade[node.netNodeFanSpeed*-1]))/2            
               
		nodeWeight[node.nId] = nw

	sortedNodeWeight = sorted(nodeWeight.items(), key=itemgetter(1))

	print "\n\nHere is printing the node Weights"
	print sortedNodeWeight

	return sortedNodeWeight

conn = MySQLdb.connect(host="172.16.1.5",user="hpc",passwd="hpc",db="hpcQoS")

# Run a MySQL query from Python and get the result set

sqlQuery = "select * from qosMain_1 JOIN (nodeCpus_1,nodeFans_1)" \
+" ON (qosMain_1.nId = nodeCpus_1.nId AND qosMain_1.nId = nodeFans_1.nId)" \
+" where qosMain_1.status like 'ON'" \
+" and (nodeCpus_1.cpuState like 'CO' or nodeCpus_1.cpuState like 'C1')"\
+" and nodeFans_1.state like 'OK'"\

conn.query(sqlQuery)

r = conn.store_result()

nodeList = createNodes(r)

for node in nodeList:
	node.display()
	node.displayNetParams()

gw = getWeights("GradeWeight.txt")
print gw

pw = getWeights("ParamsCredit.txt")
print pw	

getNodeWeights(nodeList,pw,gw)
	
conn.close()
