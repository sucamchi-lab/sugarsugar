#include <stdlib.h>

int	ft_strlen(char *str)
{
	int	i;

	i = 0;
	while (str[i])
		i++;
	return (i);
}

char	*ft_strdup(char *src)
{
	int		i;
	char	*dup;
	int		len;

	i = 0;
	len = ft_strlen(src) + 1;
	dup = malloc(len * sizeof(char));
	if (dup == NULL)
	{
		return (NULL);
	}
	while (src[i])
	{
		dup[i] = src[i];
		i++;
	}
	dup[i] = '\0';
	return (dup);
}
