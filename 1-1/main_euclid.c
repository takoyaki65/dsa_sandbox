#include <stdio.h>

int gcd_euclid(int, int);

int main(int argc, char **argv) {
  int a, b;
  scanf("%d %d", &a, &b);  
  printf("%d\n", gcd_euclid(a, b));
  return 0;
}
