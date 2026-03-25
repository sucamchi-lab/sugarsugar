#include <unistd.h>

int	main(int argc, char **argv)
{
	int	j;
	int	i;

	if (argc == 2)
	{
		i = 0;
		j = 0;
		while (argv[1][i])
		{
			if ((argv[1][i] == ' ' || argv[1][i] == '\t') && argv[1][i + 1]
				&& argv[1][i + 1] != ' ' && argv[1][i + 1] != '\t')
				j = i + 1;
			i++;
		}
		while (argv[1][j] && argv[1][j] != ' ' && argv[1][j] != '\t')
		{
			write(1, &argv[1][j], 1);
			j++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
