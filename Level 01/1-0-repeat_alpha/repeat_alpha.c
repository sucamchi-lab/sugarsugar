
#include <unistd.h>

int	letter_count(char c)
{
	if (c >= 'A' && c <= 'Z')
		return (c - 'A' + 1);
	else if (c >= 'a' && c <= 'z')
		return (c - 'a' + 1);
	else
		return (1);
}

int	main(int argc, char **argv)
{
	int	i;
	int	repeat;

	i = 0;
	if (argc == 2)
	{
		while (argv[1][i])
		{
			repeat = letter_count(argv[1][i]);
			while (repeat > 0)
			{
				write(1, &argv[1][i], 1);
				repeat--;
			}
			i++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
