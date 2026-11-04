def create_sweep_masks(nbits, ntake):

    def generate_combination(position, nbits, ntake, vector):
        if ntake == 0:
            combinations.append(vector[:])
            return
        if position == nbits:
            return

        vector[position] = 1
        generate_combination(position + 1, nbits, ntake - 1, vector)

        vector[position] = 0
        generate_combination(position + 1, nbits, ntake, vector)

    combinations = []
    initial_vector = [0] * nbits
    generate_combination(0, nbits, ntake, initial_vector)

    return combinations
