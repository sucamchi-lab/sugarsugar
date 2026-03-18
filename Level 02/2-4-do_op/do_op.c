#include <stdio.h>
#include <stdlib.h>

static void	do_op(char *nb1, char *op, char *nb2)
{
	int	left;
	int	right;
	int	result;

	left = atoi(nb1);
	right = atoi(nb2);
	result = 0;
	if (op[0] == '+')
		result = left + right;
	else if (op[0] == '-')
		result = left - right;
	else if (op[0] == '*')
		result = left * right;
	else if (op[0] == '/')
		result = left / right;
	else if (op[0] == '%')
		result = left % right;
	printf("%d\n", result);
}

int	main(int argc, char **argv)
{
	if (argc == 4)
		do_op(argv[1], argv[2], argv[3]);
	else
		printf("\n");
	return (0);
}