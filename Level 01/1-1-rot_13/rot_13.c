#include <unistd.h>

int	main(int ac, char **av)
{
	int		i;
	char	c;

	i = 0;
	if (ac == 2)
	{
		while (av[1][i])
		{
			c = av[1][i];
			if (c >= 'a' && c <= 'z')
				c = ((c - 'a' + 13) % 26) + 'a';
			else if (c >= 'A' && c <= 'Z')
				c = ((c - 'A' + 13) % 26) + 'A';
			write(1, &c, 1);
			i++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
