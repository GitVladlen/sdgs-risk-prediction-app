# -*- coding: utf-8 -*-
import os
import json

from flask import Flask, render_template

app = Flask(__name__)

# = service ===========================================================
def readData(filename):
    filepath = os.path.join("static", "data", filename)

    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    return data

def checkData(data, **filters):
    for filter_name in filters:
        filter_value = filters[filter_name]

        value = data.get(filter_name)
        if value != filter_value:
            return False
    return True

def findInData(data, **filters):
    for elem in data:
        if checkData(elem, **filters) is True:
            return elem
    return None

def selectFromData(data, **filters):
    selected = []
    for elem in data:
        if checkData(elem, **filters) is True:
            selected.append(elem)
    return selected


# = endpoints =========================================================
def goal(goal_id):
    print (" THIS IS GOAL {}.".format(goal_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    goal_tasks = selectFromData(tasks, GoalID=goal_id)

    params = dict(
        goal = goal,
        tasks = goal_tasks
    )

    return render_template('goal.html', **params)

def task(goal_id, task_id):
    print (" THIS IS TASK {}.{}.".format(goal_id, task_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    task = findInData(tasks, GoalID=goal_id, TaskID=task_id)

    indicators = readData('indicators.json')
    task_indicators = selectFromData(indicators, GoalID=goal_id, TaskID=task_id)

    params = dict(
        goal = goal,
        task = task,
        indicators = task_indicators
    )

    return render_template('task.html', **params)

def indicator(goal_id, task_id, indicator_id):
    print (" THIS IS INDICATOR {}.{}.{}.".format(goal_id, task_id, indicator_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    task = findInData(tasks, GoalID=goal_id, TaskID=task_id)

    indicators = readData('indicators.json')
    indicator = findInData(indicators, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    values = readData("values.json")
    indicator_values = selectFromData(values, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    print ("values", indicator_values)

    params = dict(
        goal = goal,
        task = task,
        indicator = indicator,
        values = indicator_values
    )

    return render_template('indicator.html', **params)


@app.route('/goal/<int:goal_id>')
@app.route('/goal/<int:goal_id>/task/<int:task_id>')
@app.route('/goal/<int:goal_id>/task/<int:task_id>/indicator/<int:indicator_id>')
def job(goal_id, task_id=None, indicator_id=None):
    if task_id is None and indicator_id is None:
        return goal(goal_id)
    elif indicator_id is None:
        return task(goal_id, task_id)
    else:
        return indicator(goal_id, task_id, indicator_id)
    

@app.route('/')
def start():

    return render_template('goals.html', goals=readData('goals.json'))