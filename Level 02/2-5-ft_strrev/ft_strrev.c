char	*ft_strrev(char *str)
{
	char	c;
	int		i;
	int		y;

	i = 0;
	while (str[i])
		i++;
	i--;
	if (i < 1)
		return (str);
	y = 0;
	while (i > y)
	{
		if (i == y)
			break ;
		c = str[i];
		str[i] = str[y];
		str[y] = c;
		i--;
		y++;
	}
	return (str);
}
