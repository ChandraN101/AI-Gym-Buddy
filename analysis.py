import matplotlib.pyplot as plt

def plot_weight_vs_days():
    # Input 1: Ask the user to input the number of days of workout
    days = int(input("Enter the number of days you worked out: "))
    
    # Initialize lists to store the day-wise data
    workout_days = []
    weights = []
    
    # Input 2: Ask the user to input their weight for each workout day
    for day in range(1, days + 1):
        weight = float(input(f"Enter your weight on day {day}: "))
        workout_days.append(day)  # Add day number to the list
        weights.append(weight)     # Add weight for that day to the list
    
    # Determine weight changes
    weight_changes = ["Initial"] + [
        "Gain" if weights[i] > weights[i - 1] else "Loss" if weights[i] < weights[i - 1] else "Same"
        for i in range(1, len(weights))
    ]

    # Plot the graph
    plt.figure(figsize=(10, 6))
    plt.plot(workout_days, weights, marker='o', linestyle='-', label='Weight Progress', color='b')
    
    # Highlighting weight gain and loss with annotations
    for i, (x, y, change) in enumerate(zip(workout_days, weights, weight_changes)):
        color = 'green' if change == "Gain" else 'red' if change == "Loss" else 'white'
        plt.annotate(f"{y} kg\n({change})", (x, y), textcoords="offset points", xytext=(0, 10), ha='center', color=color)

    # Adding titles and labels with white text
    plt.title("Weight Progress Over Days of Workout", color='white', fontsize=14)
    plt.xlabel("Days of Workout", color='white', fontsize=12)
    plt.ylabel("Weight (kg)", color='white', fontsize=12)
    
    # Style adjustments for a dark background
    plt.tick_params(colors='white')  # Tick colors
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')  # Grid color
    plt.legend(facecolor='black', edgecolor='white', labelcolor='white')  # Legend styling
    plt.tight_layout()

    # Show the graph
    plt.show()

# Call the function to plot the graph
plot_weight_vs_days()
