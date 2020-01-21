import sys

#represents one line of instruction
class Instruction:
    def __init__(self, activity, task_number, delay, resource_type, units, id):
        self.activity = activity
        self.task_number = task_number
        self.delay = int(delay)
        self.resource_type = int(resource_type)
        self.units = int(units)
        self.ID = id

#represents one individual task
class Task:
    def __init__(self, task_number, resources):
        self.aborted = False
        self.blocked = False
        self.finished = False
        self.claims = [] #only used in bankers #resources
        self.remaining = [int] * resources
        self.wait_time = 0
        self.finish_time = 0
        self.resources = setResources(resources)
        self.task_number = task_number
        self.instructions = [] #store the instructions for each task in an array

#class specifically for optimistic resource manager
class ORM:
    def __init__(self, instructions, resources):
        self.instructions = setInstructions(instructions)
        self.resources = resources
        self.release_resource = setReleaseResources(resources)
        self.cycle = 0
        self.tasks_left = len(instructions)
        self.tasks_left_temp = 0
        self.tasks = createTasksORM(instructions, resources)
        self.blocked_tasks = [Task]
        self.check_unblocked_tasks = []
        self.temp_wait = 0

#class specifically for bankers
class Banker:
    def __init__(self, instructions, resources):
        self.instructions = setInstructions(instructions)
        self.resources = resources
        self.release_resource = setReleaseResources(resources)
        self.cycle = 0
        self.tasks_left = len(instructions)
        self.tasks_left_temp = 0
        self.tasks = createTasksBankers(instructions, resources)
        self.blocked_tasks = [Task]
        self.check_unblocked_tasks = []
        self.temp_wait = 0

#this function is used to set instructions
def setInstructions(instructions):
    a = [Instruction]
    for i in instructions:
        a.append(i)
    return a

#this function is used to set up resources
def setResources(resources):
    a = []
    for i in range(resources):
        a.append(0)
    return a

#this function is used to set up release resources
def setReleaseResources(resources):
    a = []
    for i in range(len(resources)):
        a.append(0)
    return a


#this function creates tasks for ORM and returns them in the form of a list
def createTasksORM(instructions, resources):
    tasks = [Task]


    current_task_id = 1 #keep track of current task number
    for i in range(len(instructions)):

        if (instructions[i].activity == "initiate"):
            if (instructions[i].task_number != current_task_id):
                tasks.append(Task(instructions[i].task_number, len(resources)))
                current_task_id = instructions[i].task_number


    #adding the instructions to each task
    current_task_id = 1
    for i in range(len(instructions)):

        if (instructions[i].activity == "initiate"):
            continue #don't need this for ORM
        elif (instructions[i].activity == "request"):
            tasks[current_task_id].instructions.append(instructions[i])
        elif (instructions[i].activity == "release"):
            tasks[current_task_id].instructions.append(instructions[i])
        elif (instructions[i].activity == "terminate"):
            tasks[current_task_id].instructions.append(instructions[i])
            current_task_id += 1

    return tasks

#this function creates tasks for ORM and returns them in the form of a list
def createTasksBankers(instructions, resources):
    tasks = [Task]


    current_task_id = 1 #keep track of current task number
    for i in range(len(instructions)):

        if (instructions[i].activity == "initiate"):
            if (instructions[i].task_number != current_task_id):
                tasks.append(Task(instructions[i].task_number, len(resources)))
                current_task_id = instructions[i].task_number


    #adding the instructions to each task
    current_task_id = 1
    for i in range(len(instructions)):

        if (instructions[i].activity == "initiate"):
            tasks[current_task_id].instructions.append(instructions[i]) #need this instruction for bankers
        elif (instructions[i].activity == "request"):
            tasks[current_task_id].instructions.append(instructions[i])
        elif (instructions[i].activity == "release"):
            tasks[current_task_id].instructions.append(instructions[i])
        elif (instructions[i].activity == "terminate"):
            tasks[current_task_id].instructions.append(instructions[i])
            current_task_id += 1

    return tasks

#this is the function responsible for running the optimistic manager
def runORM(ORM):

    resources = ORM.resources
    tasks_left = len(ORM.tasks) - 1
    tasks_left_temp = ORM.tasks_left_temp
    instructions = ORM.instructions
    release_resource = ORM.release_resource
    cycle = ORM.cycle
    tasks = ORM.tasks
    blocked_tasks = ORM.blocked_tasks
    check_unblocked_tasks = ORM.check_unblocked_tasks
    temp_wait = ORM.temp_wait

    while (tasks_left > 0):

        tasks_left_temp = 0
        #loop through blocked tasks, see if any of their requests can be completed
        for m in range(1, len(blocked_tasks)):
            current_instruction = blocked_tasks[m].instructions[0]
            task_counter = 0
            for i in range(1, len(tasks)): #determine which task it is
                if (blocked_tasks[m].task_number == tasks[i].task_number):
                    break
                else:
                    task_counter += 1

            if (current_instruction.activity == "request"):
                #check if this request can be granted
                resource_type = (blocked_tasks[m].instructions[0].resource_type) - 1
                if (resources[resource_type] >= current_instruction.units):
                    #task can be unblocked, processes this task first
                    tasks[task_counter+1].blocked = False
                    resources[resource_type] -= current_instruction.units
                    tasks[task_counter+1].resources[resource_type] += current_instruction.units
                    check_unblocked_tasks.append(tasks[task_counter+1])
                    tasks[task_counter+1].instructions.pop(0)
                    #break
                else: #cannot be granted
                    tasks[task_counter+1].wait_time += 1
                    temp_wait += 1


        #Run through the tasks, and check for their current instruction and whether or not it can be completed
        current_instruction_index = 0 #keeps track of the index of the current instruction
        index_helper = 0

        for i in range (1, len(tasks)):

            #skip over the task if it is finished or currently blocked
            if (tasks[i].finished == True or tasks[i] in blocked_tasks):
                continue

            if (len(tasks[i].instructions) == 0):
                continue

            current_instruction = tasks[i].instructions[0]

            #check for delay, if there is a delay wait one cycle
            if (current_instruction.delay > 0):
                current_instruction.delay -= 1
            elif (current_instruction.activity == "request"):
                #check to see if the request can be granted
                resource_type = (tasks[i].instructions[0].resource_type) - 1

                #if the is more units requested then resources, deadlock
                if (current_instruction.units > resources[resource_type]):
                    blocked_tasks.append(tasks[i])
                    tasks[i].blocked = True
                    tasks[i].wait_time += 1
                    temp_wait += 1

                #Request is granted
                else:
                    resources[resource_type] -= current_instruction.units
                    tasks[i].resources[resource_type] += current_instruction.units
                    tasks[i].instructions.pop(0) #delete the instruction off the task

            elif (current_instruction.activity == "release"):
                resource_type = (tasks[i].instructions[0].resource_type) - 1
                #resources[resource_type] += current_instruction.units
                release_resource[resource_type] += current_instruction.units
                tasks[i].resources[resource_type] -= current_instruction.units
                tasks[i].instructions.pop(0)  # delete the instruction off the task

            elif (current_instruction.activity == "terminate"):
                tasks[i].finished = True
                tasks[i].finish_time = cycle + 1
                tasks_left_temp += 1
                #tasks_left -= 1

                #returning the resources
                resource_index = 0
                for i in tasks[i].resources:

                    resources[resource_index] += i
                    resource_index += 1


            index_helper += 1
            if (index_helper % 2 == 0):
                current_instruction_index += 1


        abort_task_counter = 1 #keeps track of which task to abort
        add_to_counter = False
        #If deadlock is detected, abort a task
        while (tasks_left != 0  and temp_wait == tasks_left):

            if (add_to_counter == True):
                abort_task_counter += 1

            #abort the first task
            if (tasks[abort_task_counter].finished == False):
                tasks_left -= 1
                tasks[abort_task_counter].finish_time = -1
                tasks[abort_task_counter].finished = True
                tasks[abort_task_counter].aborted = True

                #release resources from the first task
                resource_index = 0
                for j in tasks[abort_task_counter].resources:
                    resources[resource_index] += j
                    resource_index += 1
                    tasks[abort_task_counter].resources[0] = 0

                #remove it from blocked tasks
                current_task = tasks[abort_task_counter]
                for i in blocked_tasks:
                    if (i == current_task):
                        blocked_tasks.remove(i)


            #After the first task is aborted, check again to see if we need to remove another task
            temp_wait = 0
            for i in range(1, len(tasks)):
                #don't consider the task if it has already been aborted or finished
                if (tasks[i].aborted == True or tasks[i].finished == True):
                    continue
                elif (tasks[i].instructions[0].activity == "request"):
                    #check to see if the request can be granted
                    resource_type = (tasks[i].instructions[0].resource_type) - 1
                    if (resources[resource_type] >= tasks[i].instructions[0].units):
                        break
                    else:
                        temp_wait += 1
                        add_to_counter = True

        #Return resources
        for i in range(len(resources)):
            resources[i] += release_resource[i]

        #clear release_resources
        for k in range(len(release_resource)):
            release_resource[k] = 0

        delete_blocked_tasks = []  # keep track of which tasks to delete
        #clearing the already completed blocked tasks
        for j in range(len(check_unblocked_tasks)):
            current_task_id = check_unblocked_tasks[j].task_number
            for i in range(1, len(blocked_tasks)):
                if (blocked_tasks[i].task_number == current_task_id):
                    delete_blocked_tasks.append(i)


            del check_unblocked_tasks[j]

        for k in delete_blocked_tasks:
            del blocked_tasks[k]

        tasks_left -= tasks_left_temp
        temp_wait = 0
        cycle += 1

    #printing out the information
    print("FIFO")
    total_finish_time = 0
    total_wait_time = 0
    total_wait_percentage = 0
    for i in range(1, len(tasks)):

        if (tasks[i].aborted == True):
            print("Task " + str(i) + "      aborted")
        else:
            total_finish_time += tasks[i].finish_time
            total_wait_time += tasks[i].wait_time
            wait_percentage = ((tasks[i].wait_time * 100) / tasks[i].finish_time) % 100
            total_wait_percentage += wait_percentage
            print("Task " + str(i) + "      " + str(tasks[i].finish_time) + "   " + str(tasks[i].wait_time) + "   " + str(wait_percentage) + "%")

    total_wait_percentage = ((total_wait_time * 100) / total_finish_time) % 100
    print("\n")
    print("Total:")
    print("Finish time: " + str(total_finish_time))
    print("Total wait time: " + str(total_wait_time))
    print("Total wait time %: " + str(total_wait_percentage) + "%")

#This is the function for running Banker's algorithm
def runBanker(Banker):
    resources = Banker.resources
    tasks_left = len(Banker.tasks) - 1
    tasks_left_temp = Banker.tasks_left_temp
    instructions = Banker.instructions
    release_resource = Banker.release_resource
    cycle = Banker.cycle
    tasks = Banker.tasks
    blocked_tasks = Banker.blocked_tasks
    check_unblocked_tasks = Banker.check_unblocked_tasks
    temp_wait = Banker.temp_wait

    while (tasks_left > 0):

        tasks_left_temp = 0
        #loop through blocked tasks, see if any of their requests can be completed
        for m in range(1, len(blocked_tasks)):
            current_instruction = blocked_tasks[m].instructions[0]
            task_counter = 0
            for i in range(1, len(tasks)): #determine which task it is
                if (blocked_tasks[m].task_number == tasks[i].task_number):
                    break
                else:
                    task_counter += 1

            safe = True #set safe flag to true

            #go through all the claims and check if they are greater than the resource
            for i in range (0, len(resources)):
                if (blocked_tasks[m].claims[i] > resources[i]):
                    safe = False
                    break #if one found, no need to keep looking so just break out

            #go through all the instructions and check each instruction to see if it is safe
            for j in range(len(tasks[task_counter+1].instructions)):
                #resource_type = (tasks[task_counter].instructions[j].resource_type) - 1
                if(tasks[task_counter+1].instructions[j].activity == "request"):
                    max_request = tasks[task_counter+1].claims[tasks[task_counter+1].instructions[j].resource_type -1] - tasks[task_counter+1].resources[instructions[task_counter+1].resource_type - 1]
                    if (max_request > resources[resource_type]):
                        safe = False
                        break #if we find one, then we don't need to keep looking

            #if save, then proceed to grant the request
            if (safe == True):
                check_unblocked_tasks.append(tasks[task_counter+1])
                resources[current_instruction.resource_type -1] -= current_instruction.units
                blocked_tasks[m].resources[current_instruction.resource_type -1] += current_instruction.units
                tasks[task_counter+1].instructions.pop(0)

            elif (safe == False):
                tasks[task_counter+1].wait_time += 1

        for i in range (1, len(tasks)):

            #skip over the task if it is finished or currently blocked
            if (tasks[i].finished == True or tasks[i] in blocked_tasks):
                continue

            if (len(tasks[i].instructions) == 0):
                continue
            current_instruction = tasks[i].instructions[0]

            #check for delay, if there is a delay wait one cycle
            if (current_instruction.delay > 0):
                current_instruction.delay -= 1
            elif(current_instruction.activity == "initiate"):
                #Check to see if the claim > resources, abort and terminate the task
                resource_type = (tasks[i].instructions[0].resource_type) - 1
                if (resources[resource_type] < current_instruction.units):
                    tasks[i].aborted = True
                    tasks_left -= 1
                    tasks[i].finish_time = -1
                    tasks[i].finished = True
                else:
                    tasks[i].claims.insert(resource_type, current_instruction.units)
                    tasks[i].remaining[resource_type] = current_instruction.units
                    tasks[i].instructions.pop(0)

            elif (current_instruction.activity == "request"):

                resource_type = (tasks[i].instructions[0].resource_type) - 1
                #check to see if safe
                safe = True
                max_claim = tasks[i].resources[resource_type] + current_instruction.units

                #need to abort the task if the task requests more than its claim
                if (max_claim > tasks[i].claims[resource_type]):
                    tasks[i].aborted = True
                    tasks[i].finished = True
                    tasks[i].finish_time = -1
                    tasks_left_temp -= 1
                    print("During cycle " + str(cycle) + "-" + str(cycle+1) + " of Banker's Algorithms, task " + str(i) + "s request exceeded its claim")
                    #tasks_left -= 1

                    #if the task is aborted, we need to release its resources
                    for k in tasks[i].resources:
                        release_resource[k] += tasks[i].resources[k]
                        tasks[i].resources[k] = 0

                    tasks[i].instructions.pop(0)
                    continue

                #run through all the claims and make sure they can all be satisfied
                max_request = 0
                for j in range(len(tasks[i].instructions)):
                    resource_type = (tasks[i].instructions[j].resource_type) - 1
                    if (tasks[i].instructions[j].activity == "request"):
                        max_request = tasks[i].claims[resource_type] - tasks[i].resources[resource_type]

                        if(max_request > resources[resource_type]):
                            #unsafe
                            safe = False
                            tasks[i].wait_time += 1
                            blocked_tasks.append(tasks[i])
                            break

                resource_type = (tasks[i].instructions[j].resource_type) - 1
                #if the task is in a safe state, we can
                if (safe == True):
                    tasks[i].remaining[resource_type] -= current_instruction.units
                    tasks[i].resources[resource_type] += current_instruction.units
                    resources[resource_type] -= current_instruction.units
                    tasks[i].instructions.pop(0)

            elif (current_instruction.activity == "release"):
                resource_type = (tasks[i].instructions[0].resource_type) - 1
                #resources[resource_type] += current_instruction.units
                release_resource[resource_type] += current_instruction.units
                tasks[i].resources[resource_type] -= current_instruction.units
                tasks[i].instructions.pop(0)  # delete the instruction off the task

            elif (current_instruction.activity == "terminate"):
                tasks[i].finished = True
                tasks[i].finish_time = cycle + 1
                tasks_left_temp += 1
                #tasks_left -= 1

                #returning the resources
                resource_index = 0
                for i in tasks[i].resources:

                    resources[resource_index] += i
                    resource_index += 1
                #tasks[i].instructions.pop(0)

        #Return resources
        for i in range(len(resources)):
            resources[i] += release_resource[i]

        #clear release_resources
        for k in range(len(release_resource)):
            release_resource[k] = 0

        delete_blocked_tasks = []  # keep track of which tasks to delete
        #clearing the already completed blocked tasks
        for j in range(len(check_unblocked_tasks)):
            current_task_id = check_unblocked_tasks[j].task_number
            for i in range(1, len(blocked_tasks)):
                if (blocked_tasks[i].task_number == current_task_id):
                    delete_blocked_tasks.append(i)

            del check_unblocked_tasks[j]

        for k in delete_blocked_tasks:
            del blocked_tasks[k]

        tasks_left -= tasks_left_temp
        cycle += 1

    #printing out the information
    print("Bankers")
    total_finish_time = 0
    total_wait_time = 0
    total_wait_percentage = 0
    for i in range(1, len(tasks)):

        if (tasks[i].aborted == True):
            print("Task " + str(i) + "      aborted")
        else:
            total_finish_time += (tasks[i].finish_time-1)
            total_wait_time += tasks[i].wait_time
            wait_percentage = ((tasks[i].wait_time * 100) / tasks[i].finish_time) % 100
            total_wait_percentage += wait_percentage
            print("Task " + str(i) + "      " + str(tasks[i].finish_time - 1) + "   " + str(tasks[i].wait_time) + "   " + str(wait_percentage) + "%")

    total_wait_percentage = ((total_wait_time * 100) / (total_finish_time)) % 100
    print("\n")
    print("Total:")
    print("Finish time: " + str(total_finish_time))
    print("Total wait time: " + str(total_wait_time))
    print("Total wait time %: " + str(total_wait_percentage) + "%")

if __name__ == "__main__":

    user_input = sys.argv[1]
    file = open(user_input, "r")
    num_tasks = 0
    num_resources = 0
    resource_units = []
    instructions = [] #contains all the instructions which will be used for both bankers and optimistic resource manager

    file = file.readlines()
    for i in range(len(file)):
        text = file[i].split()

        if (i == 0):
            num_tasks = int(text[0])
            num_resources = int(text[1])

            for k in range (num_resources):
               resource_units.append(int(text[2 + k]))

        else:
            instructions.append(Instruction(text[0], text[1], text[2], text[3], text[4], i))

    orm_info = ORM(instructions, resource_units)
    banker_info = Banker(instructions, resource_units)
    runORM(orm_info)
    print("========================================")
    runBanker(banker_info)

