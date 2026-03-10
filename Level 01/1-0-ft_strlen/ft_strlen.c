
int	ft_strlen(char *str)
{
	int	i;

	i = 0;
	while (str[i])
		i++;
	return (i);
}

// DO NOT SUBMIT ANYTHING BELOW

#include <stdio.h>

int	main(void)
{
	char	str[] = "Flavio";

	printf("%d\n", ft_strlen(str));
	return (0);
}
