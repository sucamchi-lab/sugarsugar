#include <unistd.h>

static int	ft_strlen(char *str)
{
	int	len;

	len = 0;
	while (str[len])
	{
		len++;
	}
	return (len);
}

static int	is_pal(char *str, int start, int end)
{
	while (start < end)
	{
		if (str[start] != str[end])
		{
			return (0);
		}
		start++;
		end--;
	}
	return (1);
}

int	main(int argc, char **argv)
{
	int	start;
	int	end;
	int	best_start;
	int	best_len;
	int	len;

	if (argc != 2)
	{
		write(1, "\n", 1);
		return (0);
	}
	len = ft_strlen(argv[1]);
	best_start = 0;
	best_len = 0;
	start = 0;
	while (start < len)
	{
		end = start;
		while (end < len)
		{
			if (is_pal(argv[1], start, end) == 1)
			{
				if ((end - start + 1) > best_len || ((end - start
							+ 1) == best_len && start > best_start))
				{
					best_start = start;
					best_len = end - start + 1;
				}
			}
			end++;
		}
		start++;
	}
	write(1, argv[1] + best_start, best_len);
	write(1, "\n", 1);
	return (0);
}
