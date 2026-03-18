/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   2-0____swap_bits.c                                 :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: evgenkarlson <RTFM@42.fr>                  +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2020/02/14 12:33:14 by evgenkarlson      #+#    #+#             */
/*   Updated: 2021/02/16 23:46:11 by evgenkarlson     ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */


/* ************************************************************************** */
/* ************************************************************************** **

Assignment name  : swap_bits
Expected files   : swap_bits.c
Allowed functions:
--------------------------------------------------------------------------------

Escriba una funcion que tome un byte, intercambie el contenido de sus mitades del byte (como en el ejemplo) y devuelva el resultado.


Tu funcion deberia declararse asi:

unsigned char	swap_bits(unsigned char octet);


Ejemplo:

  1 byte
_____________
 0100 | 0001
     \ /
     / \
 0001 | 0100



/* ************************************************************************** */
/* ************************************************************************** */

unsigned char	swap_bits(unsigned char c)
{
	return ((c >> 4) | (c << 4));
}

