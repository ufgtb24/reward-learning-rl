import numpy as np

from softlearning.environments.utils import get_goal_example_environment_from_variant

DOOR_TASKS = [
    'StateSawyerDoorPullHookEnv-v0',
    'Image48SawyerDoorPullHookEnv-v0'
    ]

PUSH_TASKS = [
    'StateSawyerPushSidewaysEnv-v0',
    'Image48SawyerPushSidewaysEnv-v0',
    'StateSawyerPushForwardEnv-v0',
    'Image48SawyerPushForwardEnv-v0',
    ]

def get_goal_example_from_variant(variant):
    
    env = get_goal_example_environment_from_variant(variant)
    total_goal_examples = variant['data_params']['n_goal_examples'] \
        + variant['data_params']['n_goal_examples_validation_max']

    if variant['task'] in DOOR_TASKS:
        goal_examples = generate_door_goal_examples(total_goal_examples, env)
    elif variant['task'] in PUSH_TASKS:
        goal_examples = generate_push_goal_examples(total_goal_examples, env)
    else:
        raise NotImplementedError

    n_goal_examples = variant['data_params']['n_goal_examples']

    goal_examples_train = goal_examples[:n_goal_examples]
    goal_examples_validation = goal_examples[n_goal_examples:]

    return goal_examples_train, goal_examples_validation

def generate_push_goal_examples(total_goal_examples, env):
    max_attempt = 5*total_goal_examples
    attempts = 0
    n = 0
    goal_examples = []

    while n < total_goal_examples and attempts < max_attempt:

        attempts+= 1
        env.reset()
        goal_vec = {
            'state_desired_goal': env.unwrapped.fixed_goal
        }

        goal_vec['state_desired_goal'][:2] += np.random.uniform(low=-0.01, high=0.01, size=(2,))
        goal_vec['state_desired_goal'][-2:] += np.random.uniform(low=-0.01, high=0.01, size=(2,))
        
        env.unwrapped.set_to_goal(goal_vec)
        
        endeff_pos = env.unwrapped.get_endeff_pos()
        puck_pos = env.unwrapped.get_puck_pos()

        endeff_distance = np.linalg.norm(endeff_pos - goal_vec['state_desired_goal'][:3])
        puck_distance = np.linalg.norm(puck_pos[:2] - goal_vec['state_desired_goal'][3:5])
        puck_endeff_distance = np.linalg.norm(puck_pos[:2] - endeff_pos[:2])

        endeff_threshold = 0.05
        puck_threshold = env.unwrapped.indicator_threshold
        puck_radius = env.unwrapped.puck_radius

        if endeff_distance < endeff_threshold and puck_distance < puck_threshold and puck_endeff_distance > puck_radius:
            ob, rew, done, info = env.step(np.asarray([0.,0.]))
            goal_examples.append(ob)
            n+=1

    assert len(goal_examples) == total_goal_examples, 'Could not generate enough goal examples'
    goal_examples = np.asarray(goal_examples)

    return goal_examples

def generate_door_goal_examples(total_goal_examples, env):

    max_attempt = 5*total_goal_examples
    attempts = 0
    n = 0
    goal_examples = []

    while n < total_goal_examples and attempts < max_attempt:

        attempts+= 1
        env.reset()
        goal_vec = {
            'state_desired_goal': env.unwrapped.fixed_goal
        }

        goal_vec['state_desired_goal'][:3] += np.random.uniform(low=-0.01, high=0.01, size=(3,))
        goal_vec['state_desired_goal'][3] += np.random.uniform(low=-0.01, high=0.01)
        
        env.unwrapped.set_to_goal_pos(goal_vec['state_desired_goal'][:3])
        env.unwrapped.set_to_goal_angle(goal_vec['state_desired_goal'][3])
        
        pos = env.unwrapped.get_endeff_pos() 
        angle = env.unwrapped.get_door_angle()
        endeff_distance = np.linalg.norm(pos - goal_vec['state_desired_goal'][:3])
        angle_distance = np.abs(angle - goal_vec['state_desired_goal'][3])
        #state = np.concatenate([pos, angle])
        angle_threshold = env.unwrapped.indicator_threshold[0]
        endeff_threshold = env.unwrapped.indicator_threshold[1]

        if endeff_distance < endeff_threshold and angle_distance < angle_threshold:
            ob, rew, done, info = env.step(np.asarray([0.,0.,0.]))
            goal_examples.append(ob)
            n+=1

    assert len(goal_examples) == total_goal_examples, 'Could not generate enough goal examples'
    goal_examples = np.asarray(goal_examples)

    return goal_examples