// Simple linear congruent random number generator
// Used since Math.random() is not seedable and we want everyone
// to be using the same choice of words.
// See: https://en.wikipedia.org/wiki/Lehmer_random_number_generator
// Quality of the RNG is not really a concern

const m = 2147483647;
const a = 48271;

let seed_rng = function(seed) {
    return {'state': seed};
};

let random = function(rng_state) {
    const new_val = (a * rng_state['state'])  % m;
    rng_state['state'] = new_val;
    return new_val;
};

let choose_n = function(array, n, rng_state) {
    let chosen = [];
    let sorted_chosen = [];
    for (let i = 0; i < n; i++) {
        let length_left = array.length - i;
        let choice = random(rng_state) % length_left;
        let offset = 0;
        for (const c of sorted_chosen) {
            if (c <= choice + offset) {
                offset += 1;
            }
        }
        chosen.push(choice + offset);
        sorted_chosen.push(choice + offset);
        sorted_chosen.sort();
    }
    return chosen.map(c => array[c]);
};
