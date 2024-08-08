import random
from datetime import datetime, timedelta
from tqdm import tqdm
from .models import Device, Order, OrderProduct, Process


def get_data():
    devices = list(Device.objects.all())
    orders = list(Order.objects.all())
    order_products = OrderProduct.objects.select_related('order').all()
    processes = list(Process.objects.all())
    return devices, orders, order_products, processes


def initialize_population(population_size, processes):
    population = []
    for _ in range(population_size):
        individual = [{'process': process, 'start_time': None, 'end_time': None} for process in
                      random.sample(processes, len(processes))]
        population.append(individual)
    return population


def add_working_time(start_time, duration):
    """增加工作时间，跳过非工作时间"""

    end_time = start_time

    while duration > 0:
        work_start_morning = end_time.replace(hour=9, minute=0, second=0, microsecond=0)
        work_end_morning = end_time.replace(hour=12, minute=0, second=0, microsecond=0)
        work_start_afternoon = end_time.replace(hour=13, minute=0, second=0, microsecond=0)
        work_end_afternoon = end_time.replace(hour=18, minute=0, second=0, microsecond=0)

        if end_time < work_start_morning:
            end_time = work_start_morning
        elif end_time < work_end_morning:
            available_time = (work_end_morning - end_time).seconds / 60
            if duration <= available_time:
                end_time += timedelta(minutes=duration)
                duration = 0
            else:
                duration -= available_time
                end_time = work_start_afternoon
        elif end_time < work_start_afternoon:
            end_time = work_start_afternoon
        elif end_time < work_end_afternoon:
            available_time = (work_end_afternoon - end_time).seconds / 60
            if duration <= available_time:
                end_time += timedelta(minutes=duration)
                duration = 0
            else:
                duration -= available_time
                end_time = work_start_morning + timedelta(days=1)
        else:
            # 处理结束时间在下午工作结束后的情况
            end_time = work_start_morning + timedelta(days=1)

    return end_time


def fitness(individual, devices, orders, order_products):
    device_usage = {device.device_name: 0 for device in devices}
    order_completion_times = {order.order_code: datetime.strptime(order.order_start_date, '%Y-%m-%d') for order in
                              orders}

    for order_product in order_products:
        product_code = order_product.product_code
        order_code = order_product.order.order_code
        product_processes = [item for item in individual if item['process'].product_code == product_code]

        for item in product_processes:
            process = item['process']
            if process.is_outside:
                continue  # 跳过外包工序

            devices_list = process.device_name.split('/')  # 处理包含多个设备的情况
            for device in devices_list:
                base_name = device.split('#')[0]
                if device in device_usage:
                    device_usage[device] += process.process_duration / len(devices_list)
                elif base_name in device_usage:
                    device_usage[base_name] += process.process_duration / len(devices_list)

            start_time = order_completion_times[order_code]
            end_time = add_working_time(start_time, process.process_duration)
            order_completion_times[order_code] = end_time

            # 记录每个工序的开始和结束时间
            item['start_time'] = start_time
            item['end_time'] = end_time

    total_device_time = sum(device_usage.values())
    device_utilization = total_device_time / (len(devices) * 100)

    on_time_orders = sum(
        1 for order in orders
        if
        order_completion_times[order.order_code] <= datetime.strptime(order.order_end_date, '%Y-%m-%d').replace(hour=18,
                                                                                                                minute=0)
    )
    on_time_ratio = on_time_orders / len(orders)

    return device_utilization + on_time_ratio


def selection(population, fitness_scores):
    selected = random.choices(population, weights=fitness_scores, k=len(population) // 2)
    return selected


def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:point] + [item for item in parent2 if item not in parent1[:point]]
    child2 = parent2[:point] + [item for item in parent1 if item not in parent2[:point]]
    return child1, child2


def mutation(individual, mutation_rate):
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            swap_idx = random.randint(0, len(individual) - 1)
            individual[i], individual[swap_idx] = individual[swap_idx], individual[i]
    return individual


def evolve(population, fitness_scores, crossover_rate, mutation_rate):
    new_population = []
    selected_population = selection(population, fitness_scores)

    while len(new_population) < len(population):
        parent1 = random.choice(selected_population)
        parent2 = random.choice(selected_population)
        if random.random() < crossover_rate:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = parent1, parent2
        new_population.append(mutation(child1, mutation_rate))
        new_population.append(mutation(child2, mutation_rate))
    return new_population[:len(population)]


def genetic_algorithm(population_size, generations, crossover_rate, mutation_rate):
    devices, orders, order_products, processes = get_data()
    population = initialize_population(population_size, processes)

    for generation in tqdm(range(generations), desc="Training Progress"):
        fitness_scores = [fitness(individual, devices, orders, order_products) for individual in population]

        population = evolve(population, fitness_scores, crossover_rate, mutation_rate)
        best_fitness = max(fitness_scores)
        best_individual_index = fitness_scores.index(best_fitness)
        best_individual = population[best_individual_index]

        print(f'Generation {generation}: Best Fitness = {best_fitness}')

    return best_individual


def schedule_production():
    # 参数设置
    population_size = 50
    generations = 1
    crossover_rate = 0.8
    mutation_rate = 0.1

    # 运行遗传算法
    best_schedule = genetic_algorithm(population_size, generations, crossover_rate, mutation_rate)

    display_schedule(best_schedule)


# 输出最佳调度方案
def display_schedule(best_schedule):
    for item in best_schedule:
        process = item['process']
        start_time = item['start_time']
        end_time = item['end_time']
        print(f'Process {process.process_name} on Device {process.device_name} with Duration {process.process_duration}')
        print(f'Start Time: {start_time}, End Time: {end_time}')


if __name__ == "__main__":
    schedule_production()
