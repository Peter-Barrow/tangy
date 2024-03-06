#include "custom_vectors.h"

int main(int argc, char *argv[]) {

    vec_int* ints = vector_int_init(4);
    vector_int_push(ints, 0);
    vector_int_push(ints, 1);
    vector_int_push(ints, 2);
    vector_int_push(ints, 3);
    vector_int_push(ints, 4);

    for (int i = 0; i < ints->length; i++) {
        printf("%d,\t", ints->data[i]);
    }
    printf("\n");


}
